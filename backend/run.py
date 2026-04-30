#!/usr/bin/env python3
"""
HypeScan Token Analysis CLI Tool (Orchestrated)
Usage: python run.py <token_id> <pair_id> <chain_id>
Example: python run.py GNHW5JetZmW85vAU35KyoDcYoSd3sNWtx5RPMTDJpump 8uAAT95mo699fJ6CMpRw28DKfeVudGkonhEgmNPAEmCE solana
"""

import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from utils.formatters import print_section_header
from utils.report_generator import generate_markdown_report


async def main():
    if len(sys.argv) < 3:
        print("Usage: python run.py <token_id> <pair_id> <chain_id>")
        sys.exit(1)
        
    token_id = sys.argv[1]
    pair_id = sys.argv[2]
    chain_id = sys.argv[3]
    
    print("🚀 HypeScan Token Analysis")
    print(f"Analyzing Token: {token_id}")
    print(f"Chain: {chain_id.upper()}")
    print("")
    
    start_time = datetime.now()
    
    try:
        # Use the ReAct Orchestrator
        from core.orchestrator import orchestrator
        
        # Run orchestrated analysis
        result = await orchestrator.run(
            token_address=token_id,
            chain=chain_id,
            pair_address=pair_id
        )
        
        # Display Plan
        print_section_header("ANALYSIS PLAN")
        print(f"Reasoning: {result.plan.reasoning}")
        print(f"Data Sources: {', '.join([s.value for s in result.plan.data_sources])}")
        
        # Display Data Status
        print_section_header("DATA STATUS")
        for source, val in result.validations.items():
            status = "✓ Valid" if val.is_valid else f"✗ Skipped ({val.reason})"
            print(f"- {source.upper()}: {status}")
            
        # Display Warnings
        if result.warnings:
            print("")
            print("Warnings:")
            for w in result.warnings:
                print(f"! {w}")
        
        # Display AI Analysis Status
        print_section_header("AI ANALYSIS")
        if not result.ai_results:
            print("No AI analysis performed due to data issues.")
        else:
            for agent, data in result.ai_results.items():
                status = data.get('status', 'unknown')
                print(f"- {agent}: {status}")
                
        # Generate Report
        markdown_report = generate_markdown_report(
            token_id=token_id,
            pair_id=pair_id,
            chain_id=chain_id,
            market_data={"dex_data": result.dex_data if result.dex_data else {}},
            gmgn_data={"analysis": result.gmgn_data if result.gmgn_data else {}},
            twitter_data=result.twitter_data if result.twitter_data else {},
            ai_data=result.ai_results
        )
        
        # Save JSON results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"analysis_{token_id[:8]}_{timestamp}.json"
        
        output_data = {
            "token_id": token_id, 
            "pair_id": pair_id,
            "chain": chain_id,
            "timestamp": timestamp,
            "plan": {
                "reasoning": result.plan.reasoning,
                "sources": [s.value for s in result.plan.data_sources]
            },
            "synthesis": result.synthesis,
            "confidence": result.confidence_adjustment,
            "analysis": result.ai_results,
            "raw_data": {
                "dex": result.dex_data,
                "gmgn": result.gmgn_data,
                "twitter": result.twitter_data
            }
        }
        
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
            
        print(f"\n📁 JSON results saved to: {json_filename}")
        
        # Save Markdown report
        md_filename = f"analysis_{token_id[:8]}_{timestamp}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(markdown_report)
            
        print(f"📄 Markdown report saved to: {md_filename}")
        print(f"\n✅ Analysis complete in {(datetime.now() - start_time).total_seconds():.1f}s")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
