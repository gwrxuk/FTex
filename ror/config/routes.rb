# frozen_string_literal: true

require 'sidekiq/web'

Rails.application.routes.draw do
  # Sidekiq Web UI
  mount Sidekiq::Web => '/sidekiq'

  # Health check endpoint
  get '/health', to: 'health#show'

  # API endpoints for triggering jobs
  namespace :api do
    namespace :v1 do
      # Entity resolution
      post 'jobs/entity-resolution', to: 'jobs#entity_resolution'
      post 'jobs/entity-resolution/batch', to: 'jobs#batch_entity_resolution'

      # Network analysis
      post 'jobs/network-analysis', to: 'jobs#network_analysis'
      post 'jobs/network-generation', to: 'jobs#network_generation'

      # Risk scoring
      post 'jobs/risk-scoring', to: 'jobs#risk_scoring'
      post 'jobs/risk-scoring/batch', to: 'jobs#batch_risk_scoring'

      # Screening
      post 'jobs/screening', to: 'jobs#screening'
      post 'jobs/watchlist-sync', to: 'jobs#watchlist_sync'

      # Job status
      get 'jobs/:job_id/status', to: 'jobs#status'
    end
  end
end

