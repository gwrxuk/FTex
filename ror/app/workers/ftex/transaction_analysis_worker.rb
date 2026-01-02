# frozen_string_literal: true

module Ftex
  # Worker for analyzing transaction patterns
  class TransactionAnalysisWorker < BaseWorker
    sidekiq_options queue: :batch, retry: 3

    def perform(entity_id, options = {})
      track_job_metrics('transaction_analysis') do
        with_error_handling(entity_id: entity_id) do
          lookback_days = options['lookback_days'] || 90
          include_counterparties = options['include_counterparties'] || false

          logger.info(
            "Analyzing transactions for entity",
            entity_id: entity_id,
            lookback_days: lookback_days
          )

          # Fetch transactions from backend
          transactions = fetch_transactions(entity_id, lookback_days)

          return if transactions.blank?

          # Analyze patterns
          analysis = analyze_patterns(transactions)

          # Check for suspicious activity
          suspicious_patterns = detect_suspicious_activity(analysis)

          if suspicious_patterns.any?
            AlertWorker.perform_async(
              'suspicious_transaction',
              {
                entity_id: entity_id,
                patterns: suspicious_patterns,
                analysis: analysis
              }
            )
          end

          # Analyze counterparty networks if requested
          if include_counterparties
            analyze_counterparties(entity_id, transactions)
          end

          logger.info(
            "Transaction analysis completed",
            entity_id: entity_id,
            transaction_count: transactions.size,
            suspicious_patterns: suspicious_patterns.size
          )

          { analysis: analysis, suspicious_patterns: suspicious_patterns }
        end
      end
    end

    private

    def fetch_transactions(entity_id, lookback_days)
      api_client.get("/api/transactions", {
        entity_id: entity_id,
        from_date: (Date.today - lookback_days).iso8601,
        limit: 10_000
      })[:transactions] || []
    rescue StandardError
      []
    end

    def analyze_patterns(transactions)
      return {} if transactions.blank?

      {
        total_count: transactions.size,
        total_volume: transactions.sum { |t| t[:amount].to_f },
        average_amount: transactions.sum { |t| t[:amount].to_f } / transactions.size,
        unique_counterparties: transactions.map { |t| t[:counterparty_id] }.uniq.size,
        currencies: transactions.map { |t| t[:currency] }.tally,
        by_type: transactions.group_by { |t| t[:type] }.transform_values(&:size)
      }
    end

    def detect_suspicious_activity(analysis)
      patterns = []

      # High volume threshold
      if analysis[:total_volume].to_f > 1_000_000
        patterns << { type: 'high_volume', value: analysis[:total_volume] }
      end

      # Unusual transaction count
      if analysis[:total_count].to_i > 1000
        patterns << { type: 'high_frequency', value: analysis[:total_count] }
      end

      # Many unique counterparties could indicate structuring
      if analysis[:unique_counterparties].to_i > 100
        patterns << { type: 'many_counterparties', value: analysis[:unique_counterparties] }
      end

      patterns
    end

    def analyze_counterparties(entity_id, transactions)
      counterparty_ids = transactions.map { |t| t[:counterparty_id] }.uniq.compact

      counterparty_ids.first(50).each do |cp_id|
        # Queue network analysis for significant counterparties
        NetworkAnalysisWorker.perform_async(cp_id, { depth: 1 })
      end
    end
  end
end

