import { StoredSimulation } from '../types/simulation';

const STORAGE_KEY = 'HypeScan_simulations';
const MAX_HISTORY = 50;

export class SimulationStorage {
  /**
   * Save a completed simulation to localStorage
   */
  static saveSimulation(simulation: StoredSimulation): void {
    try {
      const simulations = this.getAllSimulations();
      
      // Add new simulation
      simulations.unshift(simulation);
      
      // Limit to MAX_HISTORY
      const limited = simulations.slice(0, MAX_HISTORY);
      
      localStorage.setItem(STORAGE_KEY, JSON.stringify(limited));
    } catch (error) {
      console.error('Failed to save simulation:', error);
      // If storage is full, try to clear old entries
      if (error instanceof DOMException && error.name === 'QuotaExceededError') {
        this.clearOldSimulations(MAX_HISTORY / 2);
        // Retry once
        try {
          const simulations = this.getAllSimulations();
          simulations.unshift(simulation);
          localStorage.setItem(STORAGE_KEY, JSON.stringify(simulations.slice(0, MAX_HISTORY)));
        } catch (retryError) {
          console.error('Failed to save simulation after cleanup:', retryError);
        }
      }
    }
  }

  /**
   * Get all stored simulations
   */
  static getAllSimulations(): StoredSimulation[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (!data) return [];
      
      const simulations = JSON.parse(data) as StoredSimulation[];
      // Convert date strings back to Date objects
      return simulations.map(sim => ({
        ...sim,
        startedAt: new Date(sim.startedAt),
        completedAt: new Date(sim.completedAt),
        prediction: {
          ...sim.prediction,
        },
        result: {
          ...sim.result,
          completedAt: new Date(sim.result.completedAt),
        },
        marketData: sim.marketData.map(snapshot => ({
          ...snapshot,
          timestamp: new Date(snapshot.timestamp),
        })),
      }));
    } catch (error) {
      console.error('Failed to load simulations:', error);
      return [];
    }
  }

  /**
   * Get a specific simulation by ID
   */
  static getSimulation(id: string): StoredSimulation | null {
    const simulations = this.getAllSimulations();
    return simulations.find(sim => sim.id === id) || null;
  }

  /**
   * Delete a simulation
   */
  static deleteSimulation(id: string): void {
    const simulations = this.getAllSimulations();
    const filtered = simulations.filter(sim => sim.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
  }

  /**
   * Clear old simulations, keeping only the most recent N
   */
  static clearOldSimulations(keepCount: number): void {
    const simulations = this.getAllSimulations();
    const limited = simulations.slice(0, keepCount);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(limited));
  }

  /**
   * Clear all simulations
   */
  static clearAll(): void {
    localStorage.removeItem(STORAGE_KEY);
  }

  /**
   * Get simulation statistics
   */
  static getStats(): {
    total: number;
    profit: number;
    loss: number;
    equilized: number;
    averagePnl: number;
    winRate: number;
  } {
    const simulations = this.getAllSimulations();
    const total = simulations.length;
    
    if (total === 0) {
      return {
        total: 0,
        profit: 0,
        loss: 0,
        equilized: 0,
        averagePnl: 0,
        winRate: 0,
      };
    }

    const profit = simulations.filter(s => s.result.status === 'profit').length;
    const loss = simulations.filter(s => s.result.status === 'loss').length;
    const equilized = simulations.filter(s => s.result.status === 'equilized').length;
    
    const totalPnl = simulations.reduce((sum, s) => sum + s.result.profitLossPercent, 0);
    const averagePnl = totalPnl / total;
    
    const winRate = (profit / total) * 100;

    return {
      total,
      profit,
      loss,
      equilized,
      averagePnl,
      winRate,
    };
  }
}
