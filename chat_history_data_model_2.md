──────────────────────────────
1. Data Model (data_model.md)
──────────────────────────────
Below is an example Markdown document that explains the design and includes some UML code for visualizing the schema.

------------------------------------------------------------
File: data_model.md
------------------------------------------------------------
# User Chat Data Model

This schema is designed to capture conversational history along with the context needed by the LLM. There are two logical entities:

• **ChatSession** – Represents a conversation started by a user. It contains metadata such as the user_id, start and end times, and an optional title.

• **ChatMessage** – Represents an individual message within a chat session. Each message includes:
  - The role (e.g. user, assistant, system, tool).
  - The content (typically the text that went to or came from the LLM).
  - Optionally, the tool information as captured by the MCP ClickHouse calls:
      ▸ tool_use – the input provided to the tool.  
      ▸ tool_response – the output from the tool (for instance, a JSON string containing a plotly visualization or a link for Grafana).

## UML Diagram

Below is a UML class diagram showing the two entities and their relationship. (Use your favorite UML renderer to visualize the following code.)

```uml
@startuml
title User Chat Data Model

class ChatSession {
  +UUID session_id
  +String user_id
  +DateTime started_at
  +Nullable(DateTime) ended_at
  +Nullable(String) title
}

class ChatMessage {
  +UUID message_id
  +UUID session_id
  +Enum role {user, assistant, system, tool}
  +String content
  +Nullable(String) tool_use
  +Nullable(String) tool_response
  +DateTime created_at
}

ChatSession "1" -- "0..*" ChatMessage : contains
@enduml
```

## Description

- **ChatSession**  
  Each session groups multiple messages and can be used to display a conversation history (similar to ChatGPT or Claude conversation lists).

- **ChatMessage**  
  In addition to storing the message content and role, each record may also include the MCP tool use and tool response information that is used as context for the LLM.

─────────────────────────────────────────────
2. ClickHouse CREATE TABLE Queries
─────────────────────────────────────────────

Below are example CREATE TABLE statements using ClickHouse's MergeTree. (You can adjust partitioning and ordering depending on your cluster/usage pattern.)

------------------------------------------------------------
-- Create table for chat sessions
------------------------------------------------------------
CREATE TABLE chat_sessions
(
    session_id UUID,
    user_id String,
    started_at DateTime,
    ended_at Nullable(DateTime),
    title Nullable(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(started_at)
ORDER BY (user_id, session_id)
SETTINGS index_granularity = 8192;

------------------------------------------------------------
-- Create table for chat messages
------------------------------------------------------------
CREATE TABLE chat_messages
(
    message_id UUID,
    session_id UUID,
    role Enum8('user' = 1, 'assistant' = 2, 'system' = 3, 'tool' = 4),
    content String,
    tool_use Nullable(String),
    tool_response Nullable(String),
    created_at DateTime
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(created_at)
ORDER BY (session_id, created_at)
SETTINGS index_granularity = 8192;

------------------------------------------------------------
Notes:
------------------------------------------------------------
• We use UUIDs for both sessions and messages.  
• The role is defined as an Enum8 with possible values; adjust these if you later add additional roles.  
• The tool_use and tool_response columns are Nullable(String) since not every message will have associated tool data.  
• DateTime columns enable proper ordering and partitioning which is critical when working with petabytes of data.

You can then query the messages for a particular session (or user) and, when needed, reassemble the conversation history for your chat UI.

This design makes it straightforward to retrieve the entire conversation history (plus the tool context for LLM response generation) when a user revisits their chat history.
