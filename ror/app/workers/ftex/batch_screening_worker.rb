# frozen_string_literal: true

module Ftex
  # Worker for batch screening entities against watchlists
  class BatchScreeningWorker < BaseWorker
    sidekiq_options queue: :batch, retry: 2

    BATCH_SIZE = 500

    def perform(entity_ids = nil)
      track_job_metrics('batch_screening') do
        entities = entity_ids ? fetch_entities(entity_ids) : fetch_all_entities

        return if entities.blank?

        logger.info("Starting batch screening for #{entities.size} entities")

        matches = []
        entities.each_slice(BATCH_SIZE) do |batch|
          batch_matches = screen_batch(batch)
          matches.concat(batch_matches)
        end

        # Create alerts for matches
        matches.each do |match|
          AlertWorker.perform_async(
            match[:match_type],
            {
              entity_id: match[:entity_id],
              matched_name: match[:matched_name],
              match_score: match[:score],
              watchlist: match[:watchlist]
            }
          )
        end

        logger.info(
          "Batch screening completed",
          screened: entities.size,
          matches: matches.size
        )

        { screened: entities.size, matches: matches.size }
      end
    end

    private

    def fetch_entities(entity_ids)
      entity_ids.map { |id| { id: id, name: '' } }
    end

    def fetch_all_entities
      # Fetch all active entities from database
      []
    end

    def screen_batch(entities)
      # Call screening service
      result = api_client.post('/api/screening/batch', {
        entities: entities.map { |e| { id: e[:id], name: e[:name] } }
      })

      result[:matches] || []
    rescue StandardError => e
      logger.error("Batch screening failed: #{e.message}")
      []
    end
  end
end

