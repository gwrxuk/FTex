# frozen_string_literal: true

class HealthController < ApplicationController
  def show
    health_status = {
      status: 'healthy',
      timestamp: Time.current.iso8601,
      checks: {
        redis: check_redis,
        database: check_database,
        sidekiq: check_sidekiq
      }
    }

    overall_healthy = health_status[:checks].values.all? { |c| c[:status] == 'ok' }
    health_status[:status] = overall_healthy ? 'healthy' : 'degraded'

    render json: health_status, status: overall_healthy ? :ok : :service_unavailable
  end

  private

  def check_redis
    Sidekiq.redis(&:ping)
    { status: 'ok' }
  rescue StandardError => e
    { status: 'error', message: e.message }
  end

  def check_database
    ActiveRecord::Base.connection.execute('SELECT 1')
    { status: 'ok' }
  rescue StandardError => e
    { status: 'error', message: e.message }
  end

  def check_sidekiq
    stats = Sidekiq::Stats.new
    {
      status: 'ok',
      processed: stats.processed,
      failed: stats.failed,
      queues: stats.queues
    }
  rescue StandardError => e
    { status: 'error', message: e.message }
  end
end

