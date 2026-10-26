from google.adk.agents import LlmAgent
from mantis.banking.llm import build_model
from mantis.banking.callbacks import sanitize_tool_call_names
from mantis.banking.front_office import build_front_office_router
from mantis.banking.mid_office import build_mid_office_router
from mantis.banking.back_office import build_back_office_router
from mantis.banking.aml_office import build_aml_office_router

def build_root_agent(mcp_session=None, mcp_tools=None, enable_aml: bool = False) -> LlmAgent:
    agent_tools = []

    if mcp_session and mcp_tools:
        # Factory function prevents Python loop late-binding issues
        def _make_tool_wrapper(tool_name: str, tool_desc: str):
            async def mcp_bridge_wrapper(**kwargs):
                # The ADK executes this, routing the request over SSE to the microservice
                result = await mcp_session.call_tool(tool_name, arguments=kwargs)
                
                # Extract text content from the MCP response object
                if hasattr(result, 'content'):
                    return "\n".join([c.text for c in result.content if hasattr(c, 'text')])
                return str(result)
            
            # Apply metadata so the LLM framework knows how to prompt the tool
            mcp_bridge_wrapper.__name__ = tool_name
            mcp_bridge_wrapper.__doc__ = tool_desc
            return mcp_bridge_wrapper

        # Dynamically generate and append all available tools
        for mcp_tool in mcp_tools:
            wrapper = _make_tool_wrapper(mcp_tool.name, mcp_tool.description)
            agent_tools.append(wrapper)

    sub_agents = [build_front_office_router(), build_mid_office_router(), build_back_office_router()]
    description = "Primary entry-point agent that routes requests into front office, mid office, or back office banking workflows."
    instruction = "You are the shared user proxy and conversable entry point for the banking operations platform. Route customer-facing requests to front_office_router. Route internal planning and representative support to mid_office_router. Route scheduled operational processing, reconciliation, and reporting to back_office_router."
    # AML office is a toggleable 4th domain (ExperimentConfig.aml_office,
    # ported from Citi_P3 -- see mantis.banking.aml_office), off by default
    # so every existing config's root agent (sub_agents, instruction,
    # description) is byte-identical to before this domain existed.
    if enable_aml:
        sub_agents.append(build_aml_office_router())
        description = "Primary entry-point agent that routes requests into front office, mid office, back office, or AML office banking workflows."
        instruction += " Route AML investigation, suspicious activity, identity-document verification, AML alert triage, and SAR drafting requests to aml_office_router -- even if the request also mentions a customer or transaction id."
    instruction += " Do not solve domain tasks yourself when a specialist workflow exists."

    return LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="user_proxy_agent",
        model=build_model("user_proxy_agent"),
        description=description,
        instruction=instruction,
        tools=agent_tools,
        sub_agents=sub_agents,
        output_key="root_routing_result",
    )
