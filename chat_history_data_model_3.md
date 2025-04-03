# User Chat Data Model  

This schema captures user chat histories and associated tool interactions for context in our Chat-to-SQL application. It consists of two main entities:  

- **ChatSession**: Represents a conversation initiated by a user, including session timeframe and an optional title.  
- **ChatMessage**: Represents each individual message in a conversation, storing message content, sender (`user` or `assistant`), and optional MCP tool data (`tool_use` & `tool_response`), which may contain Plotly visualizations or Grafana links.  

## UML Diagram  

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
  +Enum role {user, assistant}  
  +String content  
  +Nullable(String) tool_use  
  +Nullable(String) tool_response  
  +DateTime created_at  
}  

ChatSession "1" -- "0..*" ChatMessage : contains  
@enduml  
```  

## ClickHouse Table Definitions  

```sql  
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
ORDER BY (user_id, session_id);  

CREATE TABLE chat_messages  
(  
    message_id UUID,  
    session_id UUID,  
    role Enum8('user' = 1, 'assistant' = 2),  
    content String,  
    tool_use Nullable(String),  
    tool_response Nullable(String),  
    created_at DateTime  
)  
ENGINE = MergeTree  
PARTITION BY toYYYYMM(created_at)  
ORDER BY (session_id, created_at);  
```  

#### Notes:  
- UUIDs ensure unique session/message identification.  
- Roles simplified to `user` and `assistant`. No `system/tool` roles required.  
- `tool_use` and `tool_response` are optional fields capturing MCP SQL queries and responses (including Plotly or Grafana visualization data).  
- Tables partitioned monthly for performance at scale.  