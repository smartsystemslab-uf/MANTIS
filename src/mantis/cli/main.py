import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mantis.runtime.adapter import NativeBankingAdapter
from mantis.runtime.interfaces import ExperimentConfig, HookBus

SCENARIOS = {
    "front_office_monitoring": "Review transaction TXN-1001 for customer CUST-001. Run the front-office transaction monitoring, fraud, and compliance workflow and decide whether to approve or send to manual review.",
    "front_office_chatbot": "Customer asks: How do I dispute a debit card transaction and what is the expected timeline?",
    "front_office_transaction_execution": "Customer service request: Transfer 125.50 USD from source account CHK-002 to destination account EXT-998 for customer CUST-002 with memo Utility backup payment.",
    "mid_office_planning": "Use the mid-office planning workflow to analyze operations data for 2026-04-21, forecast workload, propose staffing, validate it, and provide support guidance.",
    "mid_office_rep_assist": "Representative assist request for customer CUST-001. Provide customer data, a product suggestion for idle cash, loan guidance for a home equity inquiry, and policy/risk checks.",
    "back_office_clean": "Core banking system event: Run end-of-day processing for batch EOD-2026-04-21-CLEAN and complete reconciliation and reporting.",
    "back_office_mismatch": "Core banking system event: Run end-of-day processing for batch EOD-2026-04-21-MISMATCH and handle any reconciliation mismatch according to the workflow.",
}

def _ser(obj):
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return str(obj)

async def run_scenarios(scenario_arg: str):
    selected = SCENARIOS if scenario_arg == 'all' else {scenario_arg: SCENARIOS[scenario_arg]}
    
    server_path = Path.cwd() / "citi_banking_mcp_server" / "mcp_server.py"
    if not server_path.exists():
        server_path = Path.cwd().parent / "citi_banking_mcp_server" / "mcp_server.py"
        if not server_path.exists():
             # fallback for legacy testing within the original MANTIS tree structure
             server_path = Path.cwd() / "legacy_code" / "citi_banking_mcp_server" / "mcp_server.py"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        env=os.environ.copy()
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                
                adapter = NativeBankingAdapter(mcp_session=session, mcp_tools=tools_response.tools)
                config = ExperimentConfig(workflow=scenario_arg)
                handle = adapter.build(config, HookBus())
                
                results = []
                for name, prompt in selected.items():
                    res = await handle.run_message(prompt)
                    results.append(res)
                
                print(json.dumps({name: _ser(res) for name, res in zip(selected.keys(), results)}, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Failed to connect to MCP Server: {e}", file=sys.stderr)

def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument('--scenario', choices=[*SCENARIOS.keys(), 'all'], help='Run specific scenario')
    ap.add_argument('--inventory', action='store_true', help='Print system inventory')
    args = ap.parse_args()
    
    if args.inventory:
        adapter = NativeBankingAdapter()
        inv = adapter.inventory()
        print(json.dumps(inv.model_dump(), indent=2))
        return

    if args.scenario:
        asyncio.run(run_scenarios(args.scenario))
        return
        
    ap.print_help()

if __name__ == '__main__':
    main()
