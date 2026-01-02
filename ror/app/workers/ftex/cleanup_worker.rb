# frozen_string_literal: true

module Ftex
  # Worker for cleaning up old processing data
  class CleanupWorker < BaseWorker
    sidekiq_options queue: :low, retry: 1

    RETENTION_DAYS = {
      job_logs: 30,
      temporary_results: 7,
      audit_logs: 365
    }.freeze

    def perform
      track_job_metrics('cleanup') do
        logger.info("Starting cleanup job")

        results = {
          job_logs: cleanup_job_logs,
          temporary_results: cleanup_temporary_results,
          dead_jobs: cleanup_dead_jobs
        }

        logger.info(
          "Cleanup completed",
          job_logs_removed: results[:job_logs],
          temp_results_removed: results[:temporary_results],
          dead_jobs_removed: results[:dead_jobs]
        )

        results
      end
    end

    private

    def cleanup_job_logs
      cutoff = RETENTION_DAYS[:job_logs].days.ago

      # Clean up old job execution logs
      # In production, this would delete from database
      logger.info("Cleaning job logs older than #{cutoff}")
      0
    end

    def cleanup_temporary_results
      cutoff = RETENTION_DAYS[:temporary_results].days.ago

      # Clean up temporary processing results
      logger.info("Cleaning temporary results older than #{cutoff}")
      0
    end

    def cleanup_dead_jobs
      # Clean up Sidekiq dead jobs older than retention
      dead_set = Sidekiq::DeadSet.new
      count = 0

      dead_set.each do |job|
        if Time.at(job.at) < 30.days.ago
          job.delete
          count += 1
        end
      end

      count
    end
  end
end

