# frozen_string_literal: true

module Ftex
  # Worker for batch risk scoring operations
  class BatchScoringWorker < BaseWorker
    sidekiq_options queue: :scoring, retry: 2

    BATCH_SIZE = 100

    # Process batch scoring (scheduled job)
    def perform(entity_ids = nil)
      track_job_metrics('batch_scoring') do
        entities = entity_ids ? fetch_entities(entity_ids) : fetch_entities_for_rescoring

        return if entities.blank?

        logger.info("Starting batch scoring for #{entities.size} entities")

        # Process in batches
        results = entities.each_slice(BATCH_SIZE).flat_map do |batch|
          process_batch(batch)
        end

        # Log summary
        high_risk = results.count { |r| %w[high critical].include?(r[:risk_level]) }
        avg_score = results.sum { |r| r[:overall_score] } / results.size

        logger.info(
          "Batch scoring completed",
          total: results.size,
          high_risk_count: high_risk,
          average_score: avg_score.round(3)
        )

        { processed: results.size, high_risk: high_risk, average_score: avg_score }
      end
    end

    private

    def fetch_entities(entity_ids)
      # Fetch specific entities from database
      entity_ids.map { |id| { id: id } }
    end

    def fetch_entities_for_rescoring
      # Fetch entities that need rescoring (e.g., score older than 24h, new data available)
      []
    end

    def process_batch(entities)
      result = api_client.post('/api/ftex/scoring/batch', {
        entities: entities
      })

      result[:scores] || []
    rescue StandardError => e
      logger.error("Batch scoring failed: #{e.message}")
      []
    end
  end
end

