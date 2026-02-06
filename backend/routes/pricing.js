/**
 * Pricing Routes
 * 
 * API endpoints for pricing intelligence recommendations and analysis.
 * Handles pricing data from the Python pricing intelligence engine.
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 9.1
 */

const express = require('express');
const router = express.Router();

// In-memory storage (will be replaced with database in production)
let pricingRecommendations = [];
let pricingAnalysis = [];
let reservedInstanceRecommendations = [];
let spotInstanceOpportunities = [];
let savingsPlansRecommendations = [];

/**
 * GET /api/pricing
 * Retrieve pricing intelligence recommendations with filtering
 */
router.get('/', (req, res) => {
  try {
    const { 
      recommendationType,
      service,
      region,
      minSavings,
      maxSavings,
      confidenceLevel,
      format = 'standard',
      limit = 100, 
      offset = 0 
    } = req.query;
    
    let filteredRecommendations = [...pricingRecommendations];
    
    // Apply filters
    if (recommendationType) {
      filteredRecommendations = filteredRecommendations.filter(r => r.recommendationType === recommendationType);
    }
    
    if (service) {
      filteredRecommendations = filteredRecommendations.filter(r => r.serviceType === service);
    }
    
    if (region) {
      filteredRecommendations = filteredRecommendations.filter(r => r.region === region);
    }
    
    if (minSavings) {
      filteredRecommendations = filteredRecommendations.filter(r => r.estimatedSavings >= parseFloat(minSavings));
    }
    
    if (maxSavings) {
      filteredRecommendations = filteredRecommendations.filter(r => r.estimatedSavings <= parseFloat(maxSavings));
    }
    
    if (confidenceLevel) {
      filteredRecommendations = filteredRecommendations.filter(r => r.confidenceScore >= parseFloat(confidenceLevel));
    }
    
    // Sort by estimated savings (highest first)
    filteredRecommendations.sort((a, b) => b.estimatedSavings - a.estimatedSavings);
    
    // Format data based on request type
    let responseData;
    if (format === 'chart') {
      responseData = formatPricingForCharts(filteredRecommendations);
    } else if (format === 'summary') {
      responseData = formatPricingSummary(filteredRecommendations);
    } else {
      // Apply pagination for standard format
      const startIndex = parseInt(offset);
      const endIndex = startIndex + parseInt(limit);
      responseData = filteredRecommendations.slice(startIndex, endIndex);
    }
    
    console.log(`💲 SENDING PRICING DATA: ${format} format, ${Array.isArray(responseData) ? responseData.length : 'summary'} records`);
    
    const response = {
      success: true,
      data: responseData,
      message: `Retrieved pricing recommendations in ${format} format`,
      timestamp: new Date().toISOString()
    };
    
    // Add metadata for standard format
    if (format === 'standard') {
      response.metadata = {
        total: filteredRecommendations.length,
        limit: parseInt(limit),
        offset: parseInt(offset),
        hasMore: parseInt(offset) + parseInt(limit) < filteredRecommendations.length,
        totalPotentialSavings: filteredRecommendations.reduce((sum, r) => sum + r.estimatedSavings, 0),
        filters: { recommendationType, service, region, minSavings, maxSavings, confidenceLevel }
      };
    }
    
    res.json(response);
  } catch (error) {
    console.error('❌ Error retrieving pricing recommendations:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve pricing recommendations: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/pricing
 * Submit new pricing analysis data
 */
router.post('/', (req, res) => {
  try {
    const pricingData = req.body;
    
    console.log('💲 RECEIVED PRICING DATA:', pricingData);
    
    // Validate required fields
    const requiredFields = ['recommendationType', 'serviceType', 'estimatedSavings'];
    const missingFields = requiredFields.filter(field => !pricingData[field]);
    
    if (missingFields.length > 0) {
      return res.status(400).json({
        success: false,
        data: null,
        message: `Missing required fields: ${missingFields.join(', ')}`,
        timestamp: new Date().toISOString()
      });
    }
    
    // Create pricing recommendation
    const newRecommendation = {
      recommendationId: pricingData.recommendationId || `pricing_${Date.now()}`,
      recommendationType: pricingData.recommendationType, // 'reserved_instance', 'spot_instance', 'savings_plan', 'region_migration'
      serviceType: pricingData.serviceType,
      region: pricingData.region || 'us-east-1',
      resourceId: pricingData.resourceId || '',
      currentCost: parseFloat(pricingData.currentCost || 0),
      recommendedCost: parseFloat(pricingData.recommendedCost || 0),
      estimatedSavings: parseFloat(pricingData.estimatedSavings),
      savingsPercentage: pricingData.savingsPercentage || 0,
      confidenceScore: parseFloat(pricingData.confidenceScore || 0),
      riskLevel: pricingData.riskLevel || 'MEDIUM',
      implementationEffort: pricingData.implementationEffort || 'MEDIUM',
      paybackPeriod: pricingData.paybackPeriod || 0, // months
      analysisDetails: pricingData.analysisDetails || {},
      recommendations: pricingData.recommendations || [],
      validUntil: pricingData.validUntil || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      tags: pricingData.tags || {},
      timestamp: new Date().toISOString()
    };
    
    // Check for duplicate recommendations
    const existingIndex = pricingRecommendations.findIndex(
      r => r.resourceId === newRecommendation.resourceId && 
           r.recommendationType === newRecommendation.recommendationType
    );
    
    if (existingIndex >= 0) {
      // Update existing recommendation
      pricingRecommendations[existingIndex] = newRecommendation;
      console.log('🔄 UPDATED EXISTING PRICING RECOMMENDATION:', newRecommendation.recommendationId);
    } else {
      // Add new recommendation
      pricingRecommendations.push(newRecommendation);
      console.log('➕ ADDED NEW PRICING RECOMMENDATION:', newRecommendation.recommendationId);
    }
    
    res.json({
      success: true,
      data: newRecommendation,
      message: existingIndex >= 0 ? 'Pricing recommendation updated successfully' : 'Pricing recommendation created successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error saving pricing recommendation:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to save pricing recommendation: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/pricing/reserved-instances
 * Get Reserved Instance recommendations
 */
router.get('/reserved-instances', (req, res) => {
  try {
    const { service, region, term, paymentOption } = req.query;
    
    let filteredRI = [...reservedInstanceRecommendations];
    
    // Apply filters
    if (service) {
      filteredRI = filteredRI.filter(ri => ri.serviceType === service);
    }
    
    if (region) {
      filteredRI = filteredRI.filter(ri => ri.region === region);
    }
    
    if (term) {
      filteredRI = filteredRI.filter(ri => ri.term === term);
    }
    
    if (paymentOption) {
      filteredRI = filteredRI.filter(ri => ri.paymentOption === paymentOption);
    }
    
    // Sort by ROI (highest first)
    filteredRI.sort((a, b) => b.roi - a.roi);
    
    res.json({
      success: true,
      data: filteredRI,
      message: `Retrieved ${filteredRI.length} Reserved Instance recommendations`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving RI recommendations:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve RI recommendations: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/pricing/reserved-instances
 * Create Reserved Instance recommendation
 */
router.post('/reserved-instances', (req, res) => {
  try {
    const riData = req.body;
    
    const newRI = {
      recommendationId: riData.recommendationId || `ri_${Date.now()}`,
      serviceType: riData.serviceType,
      instanceType: riData.instanceType,
      region: riData.region || 'us-east-1',
      term: riData.term || '1year', // '1year', '3year'
      paymentOption: riData.paymentOption || 'partial_upfront', // 'no_upfront', 'partial_upfront', 'all_upfront'
      currentOnDemandCost: parseFloat(riData.currentOnDemandCost),
      reservedInstanceCost: parseFloat(riData.reservedInstanceCost),
      upfrontCost: parseFloat(riData.upfrontCost || 0),
      monthlyCost: parseFloat(riData.monthlyCost),
      estimatedSavings: parseFloat(riData.estimatedSavings),
      roi: parseFloat(riData.roi || 0),
      paybackPeriod: parseFloat(riData.paybackPeriod || 0),
      utilizationRequirement: parseFloat(riData.utilizationRequirement || 0),
      currentUtilization: parseFloat(riData.currentUtilization || 0),
      confidenceScore: parseFloat(riData.confidenceScore || 0),
      riskAssessment: riData.riskAssessment || {},
      validUntil: riData.validUntil || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      timestamp: new Date().toISOString()
    };
    
    reservedInstanceRecommendations.push(newRI);
    
    res.status(201).json({
      success: true,
      data: newRI,
      message: 'Reserved Instance recommendation created successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error creating RI recommendation:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to create RI recommendation: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/pricing/spot-instances
 * Get Spot Instance opportunities
 */
router.get('/spot-instances', (req, res) => {
  try {
    const { service, region, interruptionTolerance } = req.query;
    
    let filteredSpot = [...spotInstanceOpportunities];
    
    // Apply filters
    if (service) {
      filteredSpot = filteredSpot.filter(spot => spot.serviceType === service);
    }
    
    if (region) {
      filteredSpot = filteredSpot.filter(spot => spot.region === region);
    }
    
    if (interruptionTolerance) {
      filteredSpot = filteredSpot.filter(spot => spot.interruptionTolerance === interruptionTolerance);
    }
    
    // Sort by potential savings (highest first)
    filteredSpot.sort((a, b) => b.potentialSavings - a.potentialSavings);
    
    res.json({
      success: true,
      data: filteredSpot,
      message: `Retrieved ${filteredSpot.length} Spot Instance opportunities`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving Spot Instance opportunities:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve Spot Instance opportunities: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/pricing/spot-instances
 * Create Spot Instance opportunity
 */
router.post('/spot-instances', (req, res) => {
  try {
    const spotData = req.body;
    
    const newSpot = {
      opportunityId: spotData.opportunityId || `spot_${Date.now()}`,
      serviceType: spotData.serviceType,
      instanceType: spotData.instanceType,
      region: spotData.region || 'us-east-1',
      availabilityZone: spotData.availabilityZone,
      currentOnDemandPrice: parseFloat(spotData.currentOnDemandPrice),
      currentSpotPrice: parseFloat(spotData.currentSpotPrice),
      averageSpotPrice: parseFloat(spotData.averageSpotPrice),
      potentialSavings: parseFloat(spotData.potentialSavings),
      savingsPercentage: parseFloat(spotData.savingsPercentage || 0),
      interruptionRate: parseFloat(spotData.interruptionRate || 0),
      interruptionTolerance: spotData.interruptionTolerance || 'medium', // 'low', 'medium', 'high'
      workloadSuitability: spotData.workloadSuitability || {},
      riskAssessment: spotData.riskAssessment || {},
      recommendations: spotData.recommendations || [],
      priceHistory: spotData.priceHistory || [],
      validUntil: spotData.validUntil || new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      timestamp: new Date().toISOString()
    };
    
    spotInstanceOpportunities.push(newSpot);
    
    res.status(201).json({
      success: true,
      data: newSpot,
      message: 'Spot Instance opportunity created successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error creating Spot Instance opportunity:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to create Spot Instance opportunity: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/pricing/savings-plans
 * Get Savings Plans recommendations
 */
router.get('/savings-plans', (req, res) => {
  try {
    const { planType, term, paymentOption } = req.query;
    
    let filteredSP = [...savingsPlansRecommendations];
    
    // Apply filters
    if (planType) {
      filteredSP = filteredSP.filter(sp => sp.planType === planType);
    }
    
    if (term) {
      filteredSP = filteredSP.filter(sp => sp.term === term);
    }
    
    if (paymentOption) {
      filteredSP = filteredSP.filter(sp => sp.paymentOption === paymentOption);
    }
    
    // Sort by estimated savings (highest first)
    filteredSP.sort((a, b) => b.estimatedSavings - a.estimatedSavings);
    
    res.json({
      success: true,
      data: filteredSP,
      message: `Retrieved ${filteredSP.length} Savings Plans recommendations`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving Savings Plans recommendations:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve Savings Plans recommendations: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/pricing/savings-plans
 * Create Savings Plans recommendation
 */
router.post('/savings-plans', (req, res) => {
  try {
    const spData = req.body;
    
    const newSP = {
      recommendationId: spData.recommendationId || `sp_${Date.now()}`,
      planType: spData.planType, // 'compute', 'ec2_instance', 'sagemaker'
      term: spData.term || '1year', // '1year', '3year'
      paymentOption: spData.paymentOption || 'partial_upfront',
      commitmentAmount: parseFloat(spData.commitmentAmount),
      hourlyCommitment: parseFloat(spData.hourlyCommitment),
      currentOnDemandCost: parseFloat(spData.currentOnDemandCost),
      savingsPlansRate: parseFloat(spData.savingsPlansRate),
      estimatedSavings: parseFloat(spData.estimatedSavings),
      savingsPercentage: parseFloat(spData.savingsPercentage || 0),
      utilizationRequirement: parseFloat(spData.utilizationRequirement || 0),
      currentUtilization: parseFloat(spData.currentUtilization || 0),
      coverageAnalysis: spData.coverageAnalysis || {},
      riskAssessment: spData.riskAssessment || {},
      recommendations: spData.recommendations || [],
      validUntil: spData.validUntil || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      timestamp: new Date().toISOString()
    };
    
    savingsPlansRecommendations.push(newSP);
    
    res.status(201).json({
      success: true,
      data: newSP,
      message: 'Savings Plans recommendation created successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error creating Savings Plans recommendation:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to create Savings Plans recommendation: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/pricing/chart-data
 * Get pricing data formatted for charts
 */
router.get('/chart-data', (req, res) => {
  try {
    const chartData = formatPricingForCharts(pricingRecommendations);
    
    console.log('📊 SENDING PRICING CHART DATA');
    
    res.json({
      success: true,
      data: chartData,
      message: 'Pricing chart data retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving pricing chart data:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve pricing chart data: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/pricing/summary
 * Get pricing intelligence summary
 */
router.get('/summary', (req, res) => {
  try {
    const summary = formatPricingSummary(pricingRecommendations);
    
    console.log('📈 SENDING PRICING SUMMARY');
    
    res.json({
      success: true,
      data: summary,
      message: 'Pricing summary retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving pricing summary:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve pricing summary: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * Helper function to format pricing data for charts
 */
function formatPricingForCharts(recommendations) {
  // Recommendation type breakdown
  const typeBreakdown = {};
  recommendations.forEach(rec => {
    if (!typeBreakdown[rec.recommendationType]) {
      typeBreakdown[rec.recommendationType] = {
        name: rec.recommendationType,
        value: 0,
        count: 0,
        averageConfidence: 0
      };
    }
    typeBreakdown[rec.recommendationType].value += rec.estimatedSavings;
    typeBreakdown[rec.recommendationType].count += 1;
    typeBreakdown[rec.recommendationType].averageConfidence += rec.confidenceScore;
  });
  
  // Calculate average confidence
  Object.values(typeBreakdown).forEach(type => {
    type.averageConfidence = type.count > 0 ? type.averageConfidence / type.count : 0;
  });
  
  // Service breakdown
  const serviceBreakdown = {};
  recommendations.forEach(rec => {
    if (!serviceBreakdown[rec.serviceType]) {
      serviceBreakdown[rec.serviceType] = {
        name: rec.serviceType,
        value: 0,
        count: 0
      };
    }
    serviceBreakdown[rec.serviceType].value += rec.estimatedSavings;
    serviceBreakdown[rec.serviceType].count += 1;
  });
  
  // Risk vs Savings scatter plot data
  const riskSavingsData = recommendations.map(rec => ({
    x: rec.confidenceScore,
    y: rec.estimatedSavings,
    riskLevel: rec.riskLevel,
    recommendationType: rec.recommendationType,
    serviceType: rec.serviceType
  }));
  
  return {
    typeBreakdown: Object.values(typeBreakdown),
    serviceBreakdown: Object.values(serviceBreakdown),
    riskSavingsScatter: riskSavingsData,
    totalRecommendations: recommendations.length,
    totalPotentialSavings: recommendations.reduce((sum, r) => sum + r.estimatedSavings, 0)
  };
}

/**
 * Helper function to format pricing summary
 */
function formatPricingSummary(recommendations) {
  const totalRecommendations = recommendations.length;
  const totalPotentialSavings = recommendations.reduce((sum, r) => sum + r.estimatedSavings, 0);
  const averageConfidence = totalRecommendations > 0 ? 
    recommendations.reduce((sum, r) => sum + r.confidenceScore, 0) / totalRecommendations : 0;
  
  // Type distribution
  const typeDistribution = {};
  recommendations.forEach(rec => {
    typeDistribution[rec.recommendationType] = (typeDistribution[rec.recommendationType] || 0) + rec.estimatedSavings;
  });
  
  // Risk distribution
  const riskDistribution = {};
  recommendations.forEach(rec => {
    riskDistribution[rec.riskLevel] = (riskDistribution[rec.riskLevel] || 0) + 1;
  });
  
  // Top recommendations
  const topRecommendations = [...recommendations]
    .sort((a, b) => b.estimatedSavings - a.estimatedSavings)
    .slice(0, 10);
  
  // Quick wins (high confidence, low risk, good savings)
  const quickWins = recommendations.filter(rec => 
    rec.confidenceScore >= 80 && 
    rec.riskLevel === 'LOW' && 
    rec.estimatedSavings >= 100
  );
  
  return {
    totalRecommendations,
    totalPotentialSavings,
    averageConfidence,
    typeDistribution,
    riskDistribution,
    topRecommendations,
    quickWins,
    averageSavings: totalRecommendations > 0 ? totalPotentialSavings / totalRecommendations : 0,
    lastUpdated: new Date().toISOString()
  };
}

module.exports = router;