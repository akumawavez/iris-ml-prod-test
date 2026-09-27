// $10/month budget + alert action group for rg-iris-ml-dev.
// SCOPE: resource group. Applied ONLY by scripts/setup_budget.ps1 -Confirm
// after docs/cost-tracker.md is approved. This file creates nothing by itself.
//
// What it builds:
// - Microsoft.Consumption budget "iris-dev-monthly" capped at monthlyCap USD,
//   reset monthly, tracking actual cost on the resource group.
// - Three notifications: 50% ($5), 80% ($8), 100% ($10) to contactEmails.
//   The 100% mail tells owners to run docs/teardown-and-restore.md.
// - An action group (email receivers only — no webhooks, no runbooks).

targetScope = 'resourceGroup'

@description('Monthly spend cap in USD. Team policy: 10.')
param monthlyCap int = 10

@description('Budget start date (first of the current month, yyyy-MM-dd).')
param startDate string

@description('Owner email addresses for the 50/80/100% alerts. Never commit addresses elsewhere.')
param contactEmails array

var budgetName = 'iris-dev-monthly'
var actionGroupName = 'ag-iris-dev-budget'

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: actionGroupName
  location: 'Global'
  properties: {
    groupShortName: 'irisbudget'
    enabled: true
    emailReceivers: [
      for (email, i) in contactEmails: {
        name: 'owner${i}'
        emailAddress: email
        useCommonAlertSchema: true
      }
    ]
  }
}

resource budget 'Microsoft.Consumption/budgets@2023-11-01' = {
  name: budgetName
  properties: {
    category: 'Cost'
    amount: monthlyCap
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
      endDate: '2030-12-31T00:00:00Z'
    }
    filter: {
      tags: {
        name: 'project'
        operator: 'In'
        values: [
          'iris-ml'
        ]
      }
    }
    notifications: {
      Alert50: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 50
        contactEmails: contactEmails
        contactGroups: [
          actionGroup.id
        ]
        thresholdType: 'Actual'
      }
      Alert80: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 80
        contactEmails: contactEmails
        contactGroups: [
          actionGroup.id
        ]
        thresholdType: 'Actual'
      }
      Alert100: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        contactEmails: contactEmails
        contactGroups: [
          actionGroup.id
        ]
        thresholdType: 'Actual'
      }
    }
  }
}

output budgetId string = budget.id
output actionGroupId string = actionGroup.id
