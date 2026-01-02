# frozen_string_literal: true

module Api
  module V1
    class JobsController < ApplicationController
      # POST /api/v1/jobs/entity-resolution
      def entity_resolution
        records = params[:records]
        options = params[:options] || {}

        job_id = Ftex::EntityResolutionWorker.perform_async(
          records.as_json,
          options.as_json
        )

        render json: {
          job_id: job_id,
          status: 'queued',
          job_type: 'entity_resolution',
          queued_at: Time.current.iso8601
        }, status: :accepted
      end

      # POST /api/v1/jobs/entity-resolution/batch
      def batch_entity_resolution
        entity_ids = params[:entity_ids]

        job_id = Ftex::EntityResolutionSyncWorker.perform_async

        render json: {
          job_id: job_id,
          status: 'queued',
          job_type: 'batch_entity_resolution'
        }, status: :accepted
      end

      # POST /api/v1/jobs/network-analysis
      def network_analysis
        entity_id = params.require(:entity_id)
        options = params[:options] || {}

        job_id = Ftex::NetworkAnalysisWorker.perform_async(
          entity_id,
          options.as_json
        )

        render json: {
          job_id: job_id,
          status: 'queued',
          job_type: 'network_analysis',
          entity_id: entity_id
        }, status: :accepted
      end

      # POST /api/v1/jobs/network-generation
      def network_generation
        nodes = params.require(:nodes)
        edges = params[:edges] || []
        options = params[:options] || {}

        job_id = Ftex::NetworkGenerationWorker.perform_async(
          nodes.as_json,
          edges.as_json,
          options.as_json
        )

        render json: {
          job_id: job_id,
          status: 'queued',
          job_type: 'network_generation'
        }, status: :accepted
      end

      # POST /api/v1/jobs/risk-scoring
      def risk_scoring
        entity_id = params.require(:entity_id)
        entity_data = params.require(:entity_data)
        context = params[:context] || {}

        job_id = Ftex::RiskScoringWorker.perform_async(
          entity_id,
          entity_data.as_json,
          context.as_json
        )

        render json: {
          job_id: job_id,
          status: 'queued',
          job_type: 'risk_scoring',
          entity_id: entity_id
        }, status: :accepted
      end

      # POST /api/v1/jobs/risk-scoring/batch
      def batch_risk_scoring
        entity_ids = params[:entity_ids]

        job_id = Ftex::BatchScoringWorker.perform_async(entity_ids&.as_json)

        render json: {
          job_id: job_id,
          status: 'queued',
          job_type: 'batch_risk_scoring'
        }, status: :accepted
      end

      # POST /api/v1/jobs/screening
      def screening
        entity_ids = params[:entity_ids]

        job_id = Ftex::BatchScreeningWorker.perform_async(entity_ids&.as_json)

        render json: {
          job_id: job_id,
          status: 'queued',
          job_type: 'screening'
        }, status: :accepted
      end

      # POST /api/v1/jobs/watchlist-sync
      def watchlist_sync
        sources = params[:sources]

        job_id = Ftex::WatchlistSyncWorker.perform_async(sources&.as_json)

        render json: {
          job_id: job_id,
          status: 'queued',
          job_type: 'watchlist_sync'
        }, status: :accepted
      end

      # GET /api/v1/jobs/:job_id/status
      def status
        job_id = params[:job_id]

        # Check Sidekiq for job status
        job_status = find_job_status(job_id)

        render json: job_status
      end

      private

      def find_job_status(job_id)
        # Check if job is in queue
        Sidekiq::Queue.all.each do |queue|
          queue.each do |job|
            if job.jid == job_id
              return { job_id: job_id, status: 'pending', queue: queue.name }
            end
          end
        end

        # Check if job is being processed
        Sidekiq::Workers.new.each do |_process_id, _thread_id, work|
          if work.dig('payload', 'jid') == job_id
            return { job_id: job_id, status: 'processing' }
          end
        end

        # Check retry set
        Sidekiq::RetrySet.new.each do |job|
          if job.jid == job_id
            return { job_id: job_id, status: 'retrying', retry_count: job['retry_count'] }
          end
        end

        # Check dead set
        Sidekiq::DeadSet.new.each do |job|
          if job.jid == job_id
            return { job_id: job_id, status: 'dead', error: job['error_message'] }
          end
        end

        # Job not found - could be completed
        { job_id: job_id, status: 'not_found_or_completed' }
      end
    end
  end
end

