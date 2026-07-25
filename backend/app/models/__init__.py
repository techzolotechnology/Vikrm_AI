"""
Import every model here so Alembic's autogenerate and Base.metadata
can discover them without hunting through the package.
"""
from app.models.agent import Agent  # noqa: F401
from app.models.agent_team import AgentTeam, AgentTeamRun  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.email_verification_token import EmailVerificationToken  # noqa: F401
from app.models.memory import Memory  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.password_reset_token import PasswordResetToken  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.tool_execution import ToolExecution  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.workflow import Workflow, WorkflowRun  # noqa: F401
