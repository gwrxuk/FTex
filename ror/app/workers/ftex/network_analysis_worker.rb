# frozen_string_literal: true

module Ftex
  # Worker for network/graph analysis operations
  # Builds and analyzes entity relationship networks
  class NetworkAnalysisWorker < BaseWorker
    sidekiq_options queue: :network_analysis, retry: 3

    # Analyze network for a specific entity
    # @param entity_id [String] The entity to analyze
    # @param options [Hash] Analysis options
    def perform(entity_id, options = {})
      track_job_metrics('network_analysis') do
        with_error_handling(entity_id: entity_id) do
          logger.info("Starting network analysis for entity: #{entity_id}")

          depth = options['depth'] || 2
          include_transactions = options['include_transactions'] || true

          # Get entity network from FTex backend
          result = api_client.post("/api/ftex/network/analyze/#{entity_id}", {
            depth: depth
          })

          # If high-risk connections found, trigger alerts
          check_risk_connections(entity_id, result)

          logger.info(
            "Network analysis completed",
            entity_id: entity_id,
            connections: result[:connected_entities]&.size || 0
          )

          result
        end
      end
    end

    private

    def check_risk_connections(entity_id, network_result)
      return unless network_result[:metrics]

      risk_exposure = network_result[:metrics][:risk_exposure] || 0

      if risk_exposure > 0.7
        # Queue alert creation
        AlertWorker.perform_async(
          'high_risk_network',
          {
            entity_id: entity_id,
            risk_exposure: risk_exposure,
            metrics: network_result[:metrics]
          }
        )
      end
    end
  end
end

