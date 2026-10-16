// Azure AI Foundry Evaluation Infrastructure
// Deploys: AI Foundry project, Application Insights, AI Search, Key Vault

@description('Base name for all resources')
param baseName string = 'evalaccel'

@description('Azure region for deployment')
param location string = resourceGroup().location

@description('Model deployment name')
param modelDeploymentName string = 'gpt-4o'

// ============================================================
// Application Insights (for telemetry and trace evaluation)
// ============================================================

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${baseName}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 90
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${baseName}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ============================================================
// Azure AI Search (for RAG evaluation scenarios)
// ============================================================

resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: '${baseName}-search'
  location: location
  sku: {
    name: 'basic'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
  }
}

// ============================================================
// Key Vault (for secrets management)
// ============================================================

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${baseName}-kv'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

// ============================================================
// Outputs
// ============================================================

output appInsightsConnectionString string = appInsights.properties.ConnectionString
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output searchServiceEndpoint string = 'https://${searchService.name}.search.windows.net'
output keyVaultUri string = keyVault.properties.vaultUri
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId
