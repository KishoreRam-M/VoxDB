"""Chat conversation management and routing."""

from typing import Dict, Any, Optional
from datetime import datetime
import json

from Core.Logging import logger
from Core.Config import settings
from models.domain import OperationMode, SessionContext
from services.ai_service import ai_service
from services.query_service import QueryService
from services.session_service import session_service
from db.schema import get_schema_info
from db.engine import get_engine, get_connection_key


class ChatService:
    """Orchestrate chat conversations across different modes."""

    def __init__(self):
        """Initialize chat service."""
        self.query_service = QueryService()

    async def process_chat_message(
            self,
            message: str,
            connection: Dict[str, Any],
            session_id: Optional[str],
            mode: OperationMode,
            allow_destructive: bool,
            confirm: bool
    ) -> Dict[str, Any]:
        """
        Process chat message based on operation mode.

        Args:
            message: User message
            connection: Database connection parameters
            session_id: Optional session ID
            mode: Operation mode
            allow_destructive: Allow destructive operations
            confirm: Confirmation for destructive operations

        Returns:
            Chat response dictionary
        """
        # Get or create session
        session = session_service.get_or_create(session_id)
        session_service.add_message(session.session_id, "user", message)

        # Get database connection and schema
        engine = get_engine(connection)
        conn_key = get_connection_key(connection)
        schema_info = await get_schema_info(engine, conn_key)
        session.schema_context = schema_info

        # Get chat history for context
        chat_history = session_service.get_chat_history(session.session_id)

        # Route to appropriate handler
        if mode == OperationMode.TEACHING:
            return await self._handle_teaching_mode(
                message, session, chat_history
            )

        elif mode == OperationMode.DEBUG:
            return await self._handle_debug_mode(
                message, session, chat_history
            )

        elif mode == OperationMode.SEARCH:
            return await self._handle_search_mode(
                message, session, schema_info
            )

        elif mode == OperationMode.ASSISTANT:
            return await self._handle_assistant_mode(
                message, session, schema_info, chat_history
            )

        elif mode == OperationMode.OPTIMIZATION:
            return await self._handle_optimization_mode(
                message, session, schema_info, engine,
                allow_destructive, confirm
            )

        else:  # QUERY mode (default)
            return await self._handle_query_mode(
                message, session, schema_info, engine,
                allow_destructive, confirm
            )

    async def _handle_teaching_mode(
            self,
            message: str,
            session: SessionContext,
            chat_history: list
    ) -> Dict[str, Any]:
        """Handle teaching mode conversations."""
        system_instruction = """You are OptiVox DB in Teaching Mode - The World's Best Database Educator.

CORE IDENTITY:
You are a master educator who transforms complex database concepts into crystal-clear understanding.
Your teaching approach combines deep technical expertise with exceptional pedagogical skills.

TEACHING EXCELLENCE:
✓ Break down intimidating concepts into digestible pieces
✓ Use real-world analogies that resonate with learners
✓ Build progressive understanding from fundamentals to mastery
✓ Adapt explanations to student's current knowledge level
✓ Make abstract database theory tangible and practical
✓ Inspire curiosity and deeper exploration

EDUCATIONAL METHODOLOGY:
1. ASSESS: Gauge student's current understanding
2. FOUNDATION: Establish prerequisite knowledge
3. CONCEPT: Introduce new idea with clear definition
4. CONTEXT: Explain why it matters in real-world scenarios
5. MECHANISM: Show how it works under the hood
6. EXAMPLES: Demonstrate with concrete illustrations
7. PRACTICE: Provide hands-on exercises
8. MASTERY: Challenge with progressive complexity

COMMUNICATION STYLE:
- Patient and encouraging, never condescending
- Enthusiastic about database technologies
- Use scaffolding to build understanding incrementally
- Celebrate learning milestones
- Encourage questions and critical thinking
- Connect concepts to build cohesive knowledge

CONTENT STRUCTURE:
• Clear definitions without jargon (or jargon explained)
• "Why it matters" sections for practical relevance
• Step-by-step breakdowns of processes
• Visual descriptions of data flow and relationships
• Real-world use cases and applications
• Common misconceptions and how to avoid them
• Best practices with reasoning
• Progressive exercises (easy → intermediate → advanced)
• Further exploration suggestions

You maintain conversation context to create personalized learning journeys."""

        prompt = f"""Previous learning context:
{json.dumps(chat_history[-5:], indent=2) if chat_history else "First interaction"}

Student question: {message}

Provide comprehensive educational response that:
1. Directly answers their question with clear explanation
2. Explains underlying concepts and principles
3. Gives practical, relevant examples
4. Connects to related topics they should know
5. Provides practice exercises if appropriate
6. Suggests next learning steps"""

        response_text = await ai_service.generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.7,
            max_tokens=3000
        )

        session_service.add_message(
            session.session_id,
            "assistant",
            response_text,
            {"mode": "teaching"}
        )

        logger.info(f"Teaching response generated for session {session.session_id}")

        return {
            "session_id": session.session_id,
            "mode": "teaching",
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_debug_mode(
            self,
            message: str,
            session: SessionContext,
            chat_history: list
    ) -> Dict[str, Any]:
        """Handle debug mode conversations."""
        system_instruction = """You are OptiVox DB in Expert Debug Mode - Elite Database Troubleshooter.

CORE EXPERTISE:
You are a master debugger with systematic problem-solving methodology and deep understanding
of database internals, SQL execution, and error patterns.

DEBUGGING PHILOSOPHY:
"Every bug tells a story. Our job is to read it, understand it, and resolve it."

DIAGNOSTIC CAPABILITIES:
✓ SQL syntax error interpretation and correction
✓ Logic error identification in complex queries
✓ Performance bottleneck analysis and resolution
✓ Deadlock detection and prevention strategies
✓ Data integrity issue diagnosis
✓ Connection and timeout troubleshooting
✓ Index and optimization recommendations
✓ Transaction isolation problem solving

SYSTEMATIC APPROACH:
1. LISTEN: Understand the complete problem context
2. ANALYZE: Examine error messages, symptoms, patterns
3. HYPOTHESIS: Form theories about root causes
4. DIAGNOSE: Identify the actual root cause
5. SOLVE: Provide clear, actionable solution
6. VERIFY: Suggest testing steps to confirm fix
7. PREVENT: Recommend practices to avoid recurrence

ERROR COMMUNICATION:
- Translate cryptic error messages into plain English
- Explain WHY the error occurred (root cause)
- Show WHAT needs to be fixed (specific changes)
- Demonstrate HOW to fix it (step-by-step solution)
- Discuss HOW TO AVOID it (prevention strategies)

SOLUTION QUALITY:
• Immediate fixes for urgent problems
• Proper long-term solutions following best practices
• Multiple approaches when alternatives exist
• Performance implications of each solution
• Security considerations
• Scalability impact

DEBUGGING PATTERN:
═══════════════════════════
ERROR DIAGNOSIS
───────────────────────────
What's wrong: [Clear symptom description]
Why it happens: [Root cause explanation]
Where it occurs: [Specific location in code/query]

SOLUTION
───────────────────────────
Immediate fix: [Quick resolution]
Proper solution: [Best practice approach]
Code correction: [Exact changes needed]

VERIFICATION
───────────────────────────
Testing steps: [How to verify the fix]
Expected result: [What should happen]

PREVENTION
───────────────────────────
Best practices: [How to avoid in future]
Monitoring: [What to watch for]
═══════════════════════════

Your tone is analytical, methodical, and solution-focused."""

        prompt = f"""Debug context from conversation:
{json.dumps(chat_history[-5:], indent=2) if chat_history else "New debug request"}

Debug request: {message}

Provide comprehensive debugging assistance following the systematic approach."""

        response_text = await ai_service.generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.6,
            max_tokens=2500
        )

        session_service.add_message(
            session.session_id,
            "assistant",
            response_text,
            {"mode": "debug"}
        )

        logger.info(f"Debug response generated for session {session.session_id}")

        return {
            "session_id": session.session_id,
            "mode": "debug",
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_search_mode(
            self,
            message: str,
            session: SessionContext,
            schema_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle schema search mode."""
        search_term = message.lower()

        # Search tables and columns
        search_results = {
            "tables": [
                {
                    "name": table,
                    "columns": [col["name"] for col in info["columns"]],
                    "matches": {
                        "table_name": search_term in table.lower(),
                        "columns": [
                            col["name"] for col in info["columns"]
                            if search_term in col["name"].lower()
                        ]
                    }
                }
                for table, info in schema_info["tables"].items()
                if search_term in table.lower() or
                   any(search_term in col["name"].lower() for col in info["columns"])
            ]
        }

        # Build response text
        if not search_results["tables"]:
            response_text = f"No tables or columns found matching '{message}'"
        else:
            response_text = f"Found {len(search_results['tables'])} relevant tables:\n\n"
            for table in search_results["tables"]:
                response_text += f"📊 **{table['name']}**\n"
                if table["matches"]["table_name"]:
                    response_text += f"   ✓ Table name matches\n"
                if table["matches"]["columns"]:
                    response_text += f"   ✓ Matching columns: {', '.join(table['matches']['columns'])}\n"
                response_text += f"   All columns: {', '.join(table['columns'])}\n\n"

        session_service.add_message(
            session.session_id,
            "assistant",
            response_text,
            {"mode": "search", "results": search_results}
        )

        logger.info(f"Search completed for session {session.session_id}")

        return {
            "session_id": session.session_id,
            "mode": "search",
            "response": response_text,
            "results": search_results,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_assistant_mode(
            self,
            message: str,
            session: SessionContext,
            schema_info: Dict[str, Any],
            chat_history: list
    ) -> Dict[str, Any]:
        """Handle general assistant mode."""
        system_instruction = """You are OptiVox DB - The World's Most Advanced AI Database Assistant.

CORE IDENTITY:
═══════════════════════════════════════════════════════════════
You are the pinnacle of database AI assistants, combining:
• Deep technical expertise across all database technologies
• Natural, human-like conversational abilities
• Context-aware intelligence with perfect memory
• Proactive helpfulness and insightful suggestions
• Professional excellence with approachable personality
═══════════════════════════════════════════════════════════════

KNOWLEDGE DOMAINS:
✓ SQL (MySQL, PostgreSQL, Oracle, SQL Server, SQLite, etc.)
✓ Database design, normalization, and schema architecture
✓ Query optimization and performance tuning
✓ Index strategies and execution plan analysis
✓ Transaction management and ACID properties
✓ Concurrency control and isolation levels
✓ Data modeling (ER diagrams, relational, dimensional)
✓ ETL processes and data pipelines
✓ Database security and access control
✓ Backup, recovery, and high availability
✓ Replication and sharding strategies
✓ NoSQL databases and use cases
✓ Cloud database services (AWS RDS, Azure SQL, etc.)

CAPABILITIES:
• Answer any database-related question with expertise
• Provide guidance on design decisions and trade-offs
• Explain complex concepts in accessible language
• Help users explore and understand their schemas
• Offer proactive suggestions based on context
• Maintain natural conversation flow with memory
• Adapt communication style to user's level
• Think ahead and anticipate user needs

PERSONALITY:
- Professional yet warm and approachable
- Enthusiastic about database technologies
- Patient and encouraging with all skill levels
- Articulate and concise in explanations
- Proactive in offering value-added insights
- Genuinely helpful and user-focused
- Confident without being arrogant
- Conversational and engaging

INTERACTION PRINCIPLES:
1. UNDERSTAND: Grasp the user's true intent and context
2. RESPOND: Provide accurate, relevant, complete answers
3. ENHANCE: Add value with insights and suggestions
4. GUIDE: Lead users toward best practices
5. ADAPT: Match the user's technical level
6. ENGAGE: Keep conversation natural and flowing

RESPONSE QUALITY:
• Always technically accurate and precise
• Provide working, tested solutions
• Explain reasoning behind recommendations
• Include practical examples when helpful
• Warn about potential issues or trade-offs
• Suggest related topics or follow-up questions
• Reference conversation history for continuity
• Anticipate and address unstated concerns

CONTEXT AWARENESS:
You have access to:
- User's database schema and structure
- Complete conversation history
- Previous queries and results
- User's expertise level and patterns

Use this context to provide personalized, intelligent assistance that
feels like talking to an expert colleague who knows your project."""

        # Build context-aware prompt
        schema_summary = f"Tables: {', '.join(list(schema_info['tables'].keys())[:15])}"
        if len(schema_info['tables']) > 15:
            schema_summary += f" (and {len(schema_info['tables']) - 15} more)"

        recent_context = ""
        if chat_history:
            recent = chat_history[-4:]
            recent_context = "\n\nRecent conversation:\n"
            for msg in recent:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:300]
                recent_context += f"{role.capitalize()}: {content}...\n"

        prompt = f"""Database Context:
{schema_summary}
{recent_context}

User: {message}

Respond as OptiVox DB with helpful, intelligent assistance:"""

        response_text = await ai_service.generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.8,
            max_tokens=2048
        )

        session_service.add_message(
            session.session_id,
            "assistant",
            response_text,
            {"mode": "assistant"}
        )

        logger.info(f"Assistant response generated for session {session.session_id}")

        return {
            "session_id": session.session_id,
            "mode": "assistant",
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_query_mode(
            self,
            message: str,
            session: SessionContext,
            schema_info: Dict[str, Any],
            engine,
            allow_destructive: bool,
            confirm: bool
    ) -> Dict[str, Any]:
        """Handle query execution mode."""
        result = await self.query_service.process_natural_query(
            message,
            schema_info,
            engine,
            session,
            allow_destructive,
            confirm
        )

        # Build response text
        if result.get("blocked"):
            response_text = f"⚠️ {result['message']}\n\n``````"
        elif result.get("success"):
            if result.get("query_type") == "READ":
                response_text = f"✅ Query executed successfully!\n\n``````\n\n📊 Returned {result['row_count']} rows"
            else:
                response_text = f"✅ Query executed successfully!\n\n``````\n\n✏️ Affected {result.get('rows_affected', 0)} rows"
        else:
            response_text = f"❌ Query failed!\n\n``````\n\n**Error:** {result.get('error', 'Unknown error')}"

        session_service.add_message(
            session.session_id,
            "assistant",
            response_text,
            {
                "mode": "query",
                "sql": result.get("sql"),
                "result": result
            }
        )

        logger.info(f"Query executed for session {session.session_id}")

        return {
            "session_id": session.session_id,
            "mode": "query",
            "response": response_text,
            "sql": result.get("sql"),
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_optimization_mode(
            self,
            message: str,
            session: SessionContext,
            schema_info: Dict[str, Any],
            engine,
            allow_destructive: bool,
            confirm: bool
    ) -> Dict[str, Any]:
        """Handle query optimization mode."""
        # First execute the query
        result = await self.query_service.process_natural_query(
            message,
            schema_info,
            engine,
            session,
            allow_destructive,
            confirm
        )

        if not result.get("success"):
            return await self._handle_query_mode(
                message, session, schema_info, engine,
                allow_destructive, confirm
            )

        # Generate optimization analysis
        system_instruction = """You are OptiVox DB in Query Optimization Mode - Elite Performance Specialist.

OPTIMIZATION EXPERTISE:
You are a world-class database performance expert who analyzes and optimizes queries
for maximum efficiency, scalability, and resource utilization.

ANALYSIS FRAMEWORK:
═══════════════════════════
PERFORMANCE ANALYSIS
───────────────────────────
1. Execution Pattern Analysis
   - Query execution strategy
   - Join order and methods
   - Index usage and coverage
   - Full table scans identified

2. Resource Consumption
   - CPU utilization patterns
   - I/O operations count
   - Memory usage estimates
   - Network transfer volume

3. Scalability Assessment
   - Performance at scale
   - Growth impact analysis
   - Bottleneck identification

OPTIMIZATION RECOMMENDATIONS
───────────────────────────
Priority 1: Critical improvements
Priority 2: Significant optimizations
Priority 3: Fine-tuning opportunities

For each recommendation:
✓ Specific change to implement
✓ Expected performance improvement
✓ Implementation complexity
✓ Trade-offs to consider

INDEX RECOMMENDATIONS
───────────────────────────
Indexes to CREATE:
- [Index definition with rationale]

Indexes to MODIFY:
- [Changes needed with reasoning]

Indexes to DROP:
- [Unused indexes with impact analysis]

OPTIMIZED QUERY
───────────────────────────
[Rewritten query with improvements]

Improvements made:
• [Specific optimization 1]
• [Specific optimization 2]
• [Specific optimization 3]

ALTERNATIVE APPROACHES
───────────────────────────
[Alternative query strategies if applicable]

MONITORING RECOMMENDATIONS
───────────────────────────
Key metrics to track:
- [Metric 1 and why it matters]
- [Metric 2 and why it matters]
═══════════════════════════"""

        schema_json = json.dumps(schema_info, indent=2)

        prompt = f"""Analyze and optimize this executed query:

SQL Query:

Execution Result:
- Query Type: {result.get('query_type')}
- Rows Returned: {result.get('row_count', 'N/A')}
- Rows Affected: {result.get('rows_affected', 'N/A')}
- Status: {result.get('message', 'Success')}

Database Schema:
{schema_json}

Provide comprehensive performance optimization analysis."""

        optimization_text = await ai_service.generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.5,
            max_tokens=3000
        )

        result["optimization"] = optimization_text

        response_text = f"""✅ Query executed successfully!

        📊 Result: {result.get('row_count', result.get('rows_affected', 0))} rows

        ## 🚀 Performance Optimization Analysis

        {optimization_text}"""

        session_service.add_message(
            session.session_id,
            "assistant",
            response_text,
            {
                "mode": "optimization",
                "sql": result["sql"],
                "result": result,
                "optimization": optimization_text
            }
        )

        logger.info(f"Optimization analysis generated for session {session.session_id}")

        return {
            "session_id": session.session_id,
            "mode": "optimization",
            "response": response_text,
            "sql": result["sql"],
            "result": result,
            "optimization": optimization_text,
            "timestamp": datetime.utcnow().isoformat()
        }

chat_service = ChatService()
