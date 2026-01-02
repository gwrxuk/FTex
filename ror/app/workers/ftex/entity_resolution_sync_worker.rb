# frozen_string_literal: true

module Ftex
  # Scheduled worker to sync and resolve entities from data sources
  class EntityResolutionSyncWorker < BaseWorker
    sidekiq_options queue: :entity_resolution, retry: 2

    BATCH_SIZE = 1000

    def perform
      track_job_metrics('entity_resolution_sync') do
        logger.info("Starting entity resolution sync")

        # Fetch unprocessed records from various sources
        sources = %w[crm kyc transactions watchlist]

        sources.each do |source|
          sync_source(source)
        end

        logger.info("Entity resolution sync completed")
      end
    end

    private

    def sync_source(source)
      logger.info("Syncing source: #{source}")

      # Fetch records that need resolution
      records = fetch_pending_records(source)

      return if records.blank?

      # Process in batches
      records.each_slice(BATCH_SIZE) do |batch|
        EntityResolutionWorker.perform_async(
          batch.map { |r| format_record(r, source) },
          { source: source }
        )
      end

      logger.info("Queued #{records.size} records from #{source}")
    end

    def fetch_pending_records(source)
      # In production, this would query the database for unprocessed records
      # For now, return empty - actual implementation depends on data model
      []
    end

    def format_record(record, source)
      {
        id: record[:id],
        source_system: source,
        entity_type: record[:entity_type] || 'individual',
        attributes: record[:attributes] || record
      }
    end
  end
end

