# frozen_string_literal: true

module Ftex
  # Worker for syncing sanctions and watchlists
  class WatchlistSyncWorker < BaseWorker
    sidekiq_options queue: :critical, retry: 3

    WATCHLIST_SOURCES = %w[
      ofac_sdn
      ofac_consolidated
      eu_sanctions
      un_sanctions
      pep_lists
      adverse_media
    ].freeze

    def perform(sources = nil)
      track_job_metrics('watchlist_sync') do
        sources_to_sync = sources || WATCHLIST_SOURCES

        logger.info("Starting watchlist sync for #{sources_to_sync.size} sources")

        results = {}
        sources_to_sync.each do |source|
          results[source] = sync_watchlist(source)
        end

        # Trigger rescreening of entities against updated watchlists
        queue_rescreening

        logger.info(
          "Watchlist sync completed",
          sources: results.keys,
          total_entries: results.values.sum
        )

        results
      end
    end

    private

    def sync_watchlist(source)
      logger.info("Syncing watchlist: #{source}")

      # In production, this would:
      # 1. Download latest watchlist from source
      # 2. Parse and normalize entries
      # 3. Update OpenSearch index
      # 4. Track changes

      # Simulated result
      0
    rescue StandardError => e
      logger.error("Failed to sync #{source}: #{e.message}")
      0
    end

    def queue_rescreening
      # Queue batch rescreening job for all entities
      BatchScreeningWorker.perform_async
    end
  end
end

