# frozen_string_literal: true

module Ftex
  # Worker for generating entity networks from resolved entities
  class NetworkGenerationWorker < BaseWorker
    sidekiq_options queue: :network_analysis, retry: 3

    # Generate network from a set of entities
    # @param nodes [Array<Hash>] Entity nodes
    # @param edges [Array<Hash>] Relationship edges (optional)
    # @param options [Hash] Generation options
    def perform(nodes, edges = [], options = {})
      return if nodes.blank?

      track_job_metrics('network_generation') do
        with_error_handling(node_count: nodes.size) do
          logger.info("Generating network with #{nodes.size} nodes")

          result = api_client.post('/api/ftex/network/generate', {
            nodes: nodes,
            edges: edges,
            run_inference: options['run_inference'] != false,
            transactions: options['transactions'] || []
          })

          logger.info(
            "Network generation completed",
            nodes: result.dig(:summary, :node_count) || nodes.size,
            edges: result.dig(:summary, :edge_count) || edges.size,
            inferred: result[:inferred_relationships] || 0
          )

          # Persist to Neo4j if configured
          persist_to_neo4j(result[:network]) if options['persist']

          result
        end
      end
    end

    private

    def persist_to_neo4j(network)
      return unless network

      # Neo4j persistence would happen here
      # Using the neo4j-ruby-driver gem
      logger.info("Persisting network to Neo4j")
    end
  end
end

