"""
Agentic Trading Simulation Runner.

Runs the LLM-powered autonomous trading agent on synthetic market data.
"""

import argparse
import asyncio
import json
import sys
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from .synthetic_market import SyntheticMarket, TokenSnapshot
from .agentic_trader import AgenticTrader

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


async def run_episode(
    agent: AgenticTrader,
    market: SyntheticMarket,
    episode_length: int,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run a single trading episode.
    """
    # Reset market for new episode
    snapshot = market.reset()
    equity_history = [agent.wallet.get_total_equity(snapshot.price)]
    
    trades_executed = 0
    reflections_made = 0
    last_trade_step = 0
    
    for step in range(episode_length):
        # Get market snapshot
        snapshot = market.step_market()
        
        # THINK: Agent reasons about what to do
        decision = await agent.think(snapshot)
        
        # ACT: Execute decision
        result = agent.act(decision)
        
        if result.get("executed"):
            trades_executed += 1
            last_trade_step = step
        
        # REFLECT: After trade closes, learn from it
        if result.get("executed") and decision.action == "SELL":
            pnl = result["details"].get("pnl", 0)
            reflection = await agent.reflect(result, pnl)
            if reflection:
                reflections_made += 1
        
        # Track equity
        equity = agent.wallet.get_total_equity(snapshot.price)
        equity_history.append(equity)
        
        # Progress
        if verbose and (step + 1) % 100 == 0:
            print(f"  Step {step+1}/{episode_length}: "
                  f"Equity=${equity:.2f}, "
                  f"Trades={trades_executed}")
    
    # Force close any open position
    if agent.wallet.position > 0:
        agent.wallet.sell(snapshot.price, reason="Episode ended")
        if agent.current_trade_id:
            agent.memory.close_trade(
                agent.current_trade_id,
                snapshot.price,
                "Episode ended - forced close"
            )
    
    # Calculate metrics
    initial = agent.wallet.initial_balance
    final = agent.wallet.get_total_equity(snapshot.price)
    
    return {
        "initial_equity": initial,
        "final_equity": final,
        "return_pct": ((final / initial) - 1) * 100,
        "trades": trades_executed,
        "reflections": reflections_made,
        "rules_learned": len(agent.memory.rules),
        "equity_history": equity_history,
        "action_distribution": agent.action_counts.copy()
    }


async def run_simulation(
    initial_balance: float = 100.0,
    episodes: int = 5,
    episode_length: int = 200,
    output_dir: str = None,
    seed: int = 42,
    verbose: int = 1
):
    """
    Run full agentic trading simulation.
    """
    # Setup output
    if output_dir is None:
        output_dir = Path(__file__).parent / "results" / f"agentic_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("AGENTIC TRADING SIMULATION")
    print("="*60)
    print(f"  Initial Balance:  ${initial_balance}")
    print(f"  Episodes:         {episodes}")
    print(f"  Steps/Episode:    {episode_length}")
    print(f"  Output:           {output_dir}")
    print("="*60 + "\n")
    
    # Initialize
    memory_dir = output_dir / "memory"
    agent = AgenticTrader(
        initial_balance=initial_balance,
        memory_dir=str(memory_dir),
        verbose=verbose > 1
    )
    
    market = SyntheticMarket(seed=seed)
    
    all_results = []
    
    # Run episodes
    for ep in range(episodes):
        print(f"\n[Episode {ep+1}/{episodes}]: {market.name} ({market.symbol})")
        
        # Reset agent (keep memory across episodes)
        agent.reset(keep_memory=True)
        
        # Run episode
        result = await run_episode(
            agent=agent,
            market=market,
            episode_length=episode_length,
            verbose=verbose > 0
        )
        
        all_results.append(result)
        
        print(f"  > Return: {result['return_pct']:+.2f}% | "
              f"Trades: {result['trades']} | "
              f"Rules: {result['rules_learned']}")
    
    # Generate report
    print("\n" + "="*60)
    print("SIMULATION COMPLETE")
    print("="*60)
    
    # Aggregate metrics
    avg_return = sum(r["return_pct"] for r in all_results) / len(all_results)
    total_trades = sum(r["trades"] for r in all_results)
    final_rules = all_results[-1]["rules_learned"]
    
    print(f"\n[RESULTS]:")
    print(f"  Average Return:  {avg_return:+.2f}%")
    print(f"  Best Episode:    {max(r['return_pct'] for r in all_results):+.2f}%")
    print(f"  Worst Episode:   {min(r['return_pct'] for r in all_results):+.2f}%")
    print(f"  Total Trades:    {total_trades}")
    print(f"  Rules Learned:   {final_rules}")
    
    # Save results
    summary = {
        "config": {
            "initial_balance": initial_balance,
            "episodes": episodes,
            "episode_length": episode_length,
            "seed": seed
        },
        "aggregate": {
            "avg_return_pct": avg_return,
            "best_return_pct": max(r["return_pct"] for r in all_results),
            "worst_return_pct": min(r["return_pct"] for r in all_results),
            "total_trades": total_trades,
            "rules_learned": final_rules
        },
        "episodes": [
            {k: v for k, v in r.items() if k != "equity_history"}
            for r in all_results
        ]
    }
    
    (output_dir / "results.json").write_text(json.dumps(summary, indent=2))
    
    # Save memory state
    agent.memory.save_state()
    
    print(f"\n[Output]: {output_dir}")
    print(f"  - results.json")
    print(f"  - memory/trading_journal.md")
    print(f"  - memory/trading_rules.md")
    print("="*60 + "\n")
    
    return summary


async def run_real_analysis(token_address: str, chain: str = "sol", verbose: bool = True):
    """
    Run the RL agent on a real token (single snapshot analysis).

    Args:
        token_address: Real token mint address
        chain: Blockchain chain
        verbose: Print details

    Returns:
        Dict with snapshot and agent decision
    """
    from .real_market_adapter import RealMarketAdapter

    print("\n" + "=" * 60)
    print("REAL TOKEN ANALYSIS (RL AGENT)")
    print("=" * 60)
    print(f"  Token: {token_address}")
    print(f"  Chain: {chain}")
    print("=" * 60 + "\n")

    adapter = RealMarketAdapter()
    snapshot = await adapter.get_snapshot(token_address, chain)

    if verbose:
        print(snapshot.to_market_summary())

    agent = AgenticTrader(initial_balance=100.0, verbose=verbose)
    decision = await agent.think(snapshot)

    print(f"\n[RL AGENT DECISION]")
    print(f"  Action:     {decision.action}")
    print(f"  Confidence: {decision.confidence}%")
    print(f"  Reasoning:  {decision.reasoning}")
    print(f"  Risk:       {decision.risk_assessment}")
    if decision.price_target:
        print(f"  Target:     ${decision.price_target}")
    if decision.stop_loss:
        print(f"  Stop Loss:  ${decision.stop_loss}")
    print("=" * 60 + "\n")

    return {
        "token": snapshot.to_dict(),
        "decision": {
            "action": decision.action,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "risk_assessment": decision.risk_assessment,
            "price_target": decision.price_target,
            "stop_loss": decision.stop_loss,
        }
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run Agentic Trading Simulation"
    )

    parser.add_argument(
        "--mode", type=str, default="synthetic", choices=["synthetic", "real"],
        help="Mode: 'synthetic' for simulation, 'real' for real token analysis"
    )
    parser.add_argument(
        "--token", type=str, default=None,
        help="Token address (required for --mode real)"
    )
    parser.add_argument(
        "--chain", type=str, default="sol",
        help="Blockchain chain (default: sol)"
    )
    parser.add_argument(
        "--balance", type=float, default=100.0,
        help="Initial balance (default: 100)"
    )
    parser.add_argument(
        "--episodes", type=int, default=5,
        help="Number of episodes (default: 5)"
    )
    parser.add_argument(
        "--length", type=int, default=200,
        help="Steps per episode (default: 200)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output directory"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--verbose", type=int, default=1,
        help="Verbosity level (default: 1)"
    )

    args = parser.parse_args()

    if args.mode == "real":
        if not args.token:
            parser.error("--token is required when --mode=real")
        asyncio.run(run_real_analysis(
            token_address=args.token,
            chain=args.chain,
            verbose=args.verbose > 0
        ))
    else:
        asyncio.run(run_simulation(
            initial_balance=args.balance,
            episodes=args.episodes,
            episode_length=args.length,
            output_dir=args.output,
            seed=args.seed,
            verbose=args.verbose
        ))


if __name__ == "__main__":
    main()
