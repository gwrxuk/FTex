# frozen_string_literal: true

module Ftex
  # Base worker class with common FTex functionality
  class BaseWorker
    include Sidekiq::Job

    # Default options for all FTex workers
    sidekiq_options retry: 5, backtrace: true

    # Retry with exponential backoff
    sidekiq_retry_in do |count, _exception|
      (count ** 4) + 15 + (rand(30) * (count + 1))
    end

    protected

    def api_client
      @api_client ||= Ftex::ApiClient.instance
    end

    def logger
      @logger ||= Sidekiq.logger
    end

    def with_error_handling(context = {})
      yield
    rescue Faraday::Error => e
      logger.error("API error in #{self.class.name}: #{e.message}")
      logger.error("Context: #{context}")
      raise
    rescue StandardError => e
      logger.error("Error in #{self.class.name}: #{e.message}")
      logger.error("Context: #{context}")
      logger.error(e.backtrace.first(10).join("\n"))
      raise
    end

    def track_job_metrics(job_name, &block)
      start_time = Time.current
      result = yield
      duration = Time.current - start_time

      logger.info(
        "Job completed",
        job: job_name,
        duration_ms: (duration * 1000).round(2),
        status: 'success'
      )

      result
    rescue StandardError => e
      duration = Time.current - start_time
      logger.error(
        "Job failed",
        job: job_name,
        duration_ms: (duration * 1000).round(2),
        status: 'error',
        error: e.message
      )
      raise
    end
  end
end

