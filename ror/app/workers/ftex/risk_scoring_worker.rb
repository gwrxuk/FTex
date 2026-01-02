# frozen_string_literal: true

module Ftex
  # Worker for calculating contextual risk scores
  class RiskScoringWorker < BaseWorker
    sidekiq_options queue: :scoring, retry: 3

    # Calculate risk score for an entity
    # @param entity_id [String] Entity identifier
    # @param entity_data [Hash] Entity attributes
    # @param context [Hash] Additional context for scoring
    def perform(entity_id, entity_data, context = {})
      track_job_metrics('risk_scoring') do
        with_error_handling(entity_id: entity_id) do
          logger.info("Calculating risk score for entity: #{entity_id}")

          entity = entity_data.merge('id' => entity_id)

          result = api_client.post('/api/ftex/scoring/calculate', {
            entity: entity,
            context: context
          })

          risk_level = result[:risk_level]
          score = result[:overall_score]

          logger.info(
            "Risk scoring completed",
            entity_id: entity_id,
            score: score,
            level: risk_level
          )

          # Handle based on risk level
          handle_risk_result(entity_id, result)

          result
        end
      end
    end

    private

    def handle_risk_result(entity_id, result)
      case result[:risk_level]
      when 'critical', 'high'
        # Create high priority alert
        AlertWorker.perform_async(
          'high_risk_entity',
          {
            entity_id: entity_id,
            score: result[:overall_score],
            risk_level: result[:risk_level],
            explanation: result[:explanation]
          },
          { priority: 'critical' }
        )
      when 'medium'
        # Queue for enhanced due diligence
        EnhancedDueDiligenceWorker.perform_async(entity_id)
      end
    end
  end
end

