# frozen_string_literal: true

module Ftex
  # Worker for creating and managing alerts
  class AlertWorker < BaseWorker
    sidekiq_options queue: :critical, retry: 5

    ALERT_TYPES = {
      'high_risk_entity' => { priority: 'high', category: 'risk' },
      'high_risk_network' => { priority: 'high', category: 'network' },
      'watchlist_match' => { priority: 'critical', category: 'compliance' },
      'suspicious_transaction' => { priority: 'high', category: 'transaction' },
      'pep_match' => { priority: 'medium', category: 'compliance' },
      'sanctions_match' => { priority: 'critical', category: 'compliance' }
    }.freeze

    # Create an alert
    # @param alert_type [String] Type of alert
    # @param data [Hash] Alert data
    # @param options [Hash] Additional options
    def perform(alert_type, data, options = {})
      track_job_metrics('alert_creation') do
        with_error_handling(alert_type: alert_type) do
          alert_config = ALERT_TYPES[alert_type] || { priority: 'medium', category: 'other' }

          priority = options['priority'] || alert_config[:priority]
          category = alert_config[:category]

          logger.info(
            "Creating alert",
            type: alert_type,
            priority: priority,
            entity_id: data['entity_id']
          )

          # Call backend to create alert
          result = api_client.post('/api/alerts', {
            alert_type: alert_type,
            priority: priority,
            category: category,
            entity_id: data['entity_id'],
            data: data,
            status: 'open',
            created_at: Time.current.iso8601
          })

          # Notify if critical
          notify_critical_alert(alert_type, data) if priority == 'critical'

          result
        end
      end
    end

    private

    def notify_critical_alert(alert_type, data)
      logger.warn(
        "CRITICAL ALERT",
        type: alert_type,
        entity_id: data['entity_id']
      )

      # In production, this would:
      # - Send email notifications
      # - Push to Slack/Teams
      # - Trigger PagerDuty
    end
  end
end

