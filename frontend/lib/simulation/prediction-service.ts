import { TokenSnapshot, TradeDecision } from '../types/simulation';

/**
 * Mock prediction service that mimics the backend RL agent's decision logic
 */
export class PredictionService {
  /**
   * Generate a trading decision based on token snapshot
   * This mirrors the backend AgenticTrader's think() method
   */
  static async generatePrediction(
    snapshot: TokenSnapshot,
    currentPrice: number,
    duration: number // minutes
  ): Promise<TradeDecision> {
    // Simulate analysis delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Analyze technical indicators
    const rsiSignal = snapshot.rsi < 30 ? 1 : snapshot.rsi > 70 ? -1 : 0;
    const macdSignal = snapshot.macd > snapshot.macdSignal ? 1 : -1;
    const bollingerSignal = snapshot.bollingerPosition < -0.8 ? 1 : snapshot.bollingerPosition > 0.8 ? -1 : 0;
    
    // Analyze on-chain safety
    const rugScoreSignal = snapshot.rugScore < 30 ? 1 : snapshot.rugScore > 70 ? -1 : 0;
    const liquiditySignal = snapshot.liquidityLocked ? 1 : -0.5;
    const smartMoneySignal = snapshot.smartMoneyFlow === 'buying' ? 1 : snapshot.smartMoneyFlow === 'selling' ? -1 : 0;
    
    // Analyze social sentiment
    const sentimentSignal = snapshot.sentimentScore > 70 ? 1 : snapshot.sentimentScore < 30 ? -1 : 0;
    const trendingSignal = snapshot.trending ? 0.5 : 0;
    
    // Combine signals
    const technicalScore = (rsiSignal + macdSignal + bollingerSignal) / 3;
    const onChainScore = (rugScoreSignal * 0.5 + liquiditySignal * 0.3 + smartMoneySignal * 0.2);
    const socialScore = (sentimentSignal * 0.7 + trendingSignal * 0.3);
    
    const overallScore = (technicalScore * 0.4 + onChainScore * 0.4 + socialScore * 0.2);
    
    // Determine action
    let action: 'BUY' | 'SELL' | 'HOLD';
    let confidence: number;
    let reasoning: string;
    let riskAssessment: string;
    
    if (overallScore > 0.3 && snapshot.rugScore < 50) {
      action = 'BUY';
      confidence = Math.min(95, Math.max(50, Math.round(overallScore * 100 + 30)));
      reasoning = this.generateBuyReasoning(snapshot, technicalScore, onChainScore, socialScore);
      riskAssessment = this.assessRisk(snapshot, 'BUY');
    } else if (overallScore < -0.3) {
      action = 'SELL';
      confidence = Math.min(95, Math.max(50, Math.round(Math.abs(overallScore) * 100 + 30)));
      reasoning = this.generateSellReasoning(snapshot, technicalScore, onChainScore, socialScore);
      riskAssessment = this.assessRisk(snapshot, 'SELL');
    } else {
      action = 'HOLD';
      confidence = Math.round(Math.abs(overallScore) * 50 + 30);
      reasoning = 'Market signals are mixed. Waiting for clearer entry/exit signals.';
      riskAssessment = 'Moderate risk due to uncertain market conditions.';
    }
    
    // Calculate predicted price
    const volatility = snapshot.volatility;
    const priceChange = overallScore * volatility * duration * 0.1; // Scale by duration
    const predictedValue = currentPrice * (1 + priceChange);
    
    // Add some variance (±5-10%)
    const variance = (Math.random() - 0.5) * 0.1;
    const finalPredictedValue = predictedValue * (1 + variance);
    
    const priceTarget = action === 'BUY' ? finalPredictedValue * 1.1 : undefined;
    const stopLoss = action === 'BUY' ? currentPrice * 0.9 : undefined;
    
    return {
      action,
      confidence,
      reasoning,
      riskAssessment,
      priceTarget,
      stopLoss,
      predictedValue: finalPredictedValue,
    };
  }
  
  private static generateBuyReasoning(
    snapshot: TokenSnapshot,
    technical: number,
    onChain: number,
    social: number
  ): string {
    const reasons: string[] = [];
    
    if (snapshot.rsi < 30) reasons.push('RSI indicates oversold conditions');
    if (snapshot.macd > snapshot.macdSignal) reasons.push('MACD shows bullish momentum');
    if (snapshot.bollingerPosition < -0.8) reasons.push('Price near lower Bollinger Band');
    if (snapshot.smartMoneyFlow === 'buying') reasons.push('Smart money is accumulating');
    if (snapshot.rugScore < 30) reasons.push('Low rug score indicates safety');
    if (snapshot.liquidityLocked) reasons.push('Liquidity is locked');
    if (snapshot.sentimentScore > 70) reasons.push('Strong positive sentiment');
    if (snapshot.trending) reasons.push('Token is trending');
    
    if (reasons.length === 0) {
      return 'Multiple technical and on-chain indicators suggest buying opportunity.';
    }
    
    return reasons.slice(0, 3).join(', ') + '.';
  }
  
  private static generateSellReasoning(
    snapshot: TokenSnapshot,
    technical: number,
    onChain: number,
    social: number
  ): string {
    const reasons: string[] = [];
    
    if (snapshot.rsi > 70) reasons.push('RSI indicates overbought conditions');
    if (snapshot.macd < snapshot.macdSignal) reasons.push('MACD shows bearish momentum');
    if (snapshot.bollingerPosition > 0.8) reasons.push('Price near upper Bollinger Band');
    if (snapshot.smartMoneyFlow === 'selling') reasons.push('Smart money is distributing');
    if (snapshot.rugScore > 70) reasons.push('High rug score indicates risk');
    if (snapshot.sentimentScore < 30) reasons.push('Negative sentiment');
    
    if (reasons.length === 0) {
      return 'Multiple indicators suggest taking profits or avoiding entry.';
    }
    
    return reasons.slice(0, 3).join(', ') + '.';
  }
  
  private static assessRisk(snapshot: TokenSnapshot, action: 'BUY' | 'SELL'): string {
    const risks: string[] = [];
    
    if (snapshot.rugScore > 60) {
      risks.push('High rug score');
    }
    if (!snapshot.liquidityLocked) {
      risks.push('Liquidity not locked');
    }
    if (snapshot.devWalletPct > 20) {
      risks.push('High dev wallet concentration');
    }
    if (snapshot.top10HolderPct > 40) {
      risks.push('High holder concentration');
    }
    if (snapshot.volatility > 0.15) {
      risks.push('High volatility');
    }
    
    if (risks.length === 0) {
      return 'Risk factors appear manageable.';
    }
    
    return `Key risks: ${risks.slice(0, 2).join(', ')}.`;
  }
}
