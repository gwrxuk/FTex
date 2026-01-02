# frozen_string_literal: true

module Ftex
  # Worker for processing entity resolution jobs
  # Resolves entities across multiple data sources using FTex's core capabilities
  class EntityResolutionWorker < BaseWorker
    sidekiq_options queue: :entity_resolution, retry: 3

    # Process a batch of entity records for resolution
    # @param records [Array<Hash>] Array of entity records to resolve
    # @param options [Hash] Resolution options
    def perform(records, options = {})
      return if records.blank?

      track_job_metrics('entity_resolution') do
        with_error_handling(record_count: records.size) do
          logger.info("Starting entity resolution for #{records.size} records")

          # Call FTex backend API for entity resolution
          result = api_client.post('/api/ftex/entity-resolution', {
            records: records,
            match_threshold: options['match_threshold'] || 0.75,
            blocking_strategies: options['blocking_strategies'] || %w[soundex ngram]
          })

          logger.info(
            "Entity resolution completed",
            input_count: result[:input_record_count],
            resolved_count: result[:resolved_entity_count],
            resolution_rate: result[:resolution_rate]
          )

          # Store results or trigger downstream jobs
          process_resolution_results(result[:resolved_entities])

          result
        end
      end
    end

    private

    def process_resolution_results(entities)
      return if entities.blank?

      entities.each do |entity|
        # Trigger network analysis for high-confidence matches
        if entity[:confidence_score] >= 0.85
          NetworkAnalysisWorker.perform_async(
            entity[:resolved_id],
            { depth: 2, include_transactions: true }
          )
        end

        # Trigger risk scoring
        RiskScoringWorker.perform_async(
          entity[:resolved_id],
          entity[:attributes]
        )
      end
    end
  end
end

