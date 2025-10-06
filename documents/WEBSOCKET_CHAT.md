# 🔌 WebSocket Real-time Chat

Complete guide for implementing real-time chat with WebSocket in Flutter.

---

## 📋 Overview

WebSocket features:
- **Real-time messaging**: Instant message delivery
- **Typing indicators**: See when someone is typing
- **Read receipts**: Know when messages are read
- **Auto-reconnection**: Handles connection drops
- **JWT Authentication**: Secure connections

---

## 🔌 WebSocket URL

```
ws://localhost:8000/ws/chat/{chat_id}/?token=<jwt_access_token>
```

**Production:**
```
wss://yourdomain.com/ws/chat/{chat_id}/?token=<jwt_access_token>
```

---

## 📱 Flutter Implementation

### 1. Add Dependency

```yaml
# pubspec.yaml
dependencies:
  web_socket_channel: ^2.4.0
```

### 2. WebSocket Service

```dart
// services/chat_websocket_service.dart
import 'dart:convert';
import 'dart:async';
import 'package:web_socket_channel/web_socket_channel.dart';

class ChatWebSocketService {
  WebSocketChannel? _channel;
  StreamController<ChatEvent>? _eventController;
  Timer? _reconnectTimer;
  
  final int chatId;
  final String accessToken;
  final String baseUrl;
  
  bool _shouldReconnect = true;
  int _reconnectAttempts = 0;
  static const int _maxReconnectAttempts = 5;
  
  ChatWebSocketService({
    required this.chatId,
    required this.accessToken,
    this.baseUrl = 'ws://localhost:8000',
  });
  
  Stream<ChatEvent> get events {
    _eventController ??= StreamController<ChatEvent>.broadcast();
    return _eventController!.stream;
  }
  
  void connect() {
    if (_reconnectAttempts >= _maxReconnectAttempts) {
      print('Max reconnection attempts reached');
      return;
    }
    
    try {
      final uri = Uri.parse('$baseUrl/ws/chat/$chatId/?token=$accessToken');
      _channel = WebSocketChannel.connect(uri);
      
      _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
        cancelOnError: false,
      );
      
      // Reset reconnect attempts on successful connection
      _reconnectAttempts = 0;
      
      print('WebSocket connected');
    } catch (e) {
      print('Connection error: $e');
      _attemptReconnect();
    }
  }
  
  void _onMessage(dynamic data) {
    try {
      final json = jsonDecode(data);
      final type = json['type'];
      
      switch (type) {
        case 'connection_established':
          _eventController?.add(ConnectionEstablished());
          break;
          
        case 'chat_message':
          _eventController?.add(NewMessage(
            id: json['message']['id'],
            senderId: json['message']['sender_id'],
            senderName: json['message']['sender_name'],
            content: json['message']['content'],
            messageType: json['message']['message_type'],
            createdAt: DateTime.parse(json['message']['created_at']),
            isRead: json['message']['is_read'],
          ));
          break;
          
        case 'typing_indicator':
          _eventController?.add(TypingIndicator(
            userId: json['user_id'],
            userName: json['user_name'],
            isTyping: json['is_typing'],
          ));
          break;
          
        case 'read_receipt':
          _eventController?.add(ReadReceipt(
            messageId: json['message_id'],
            userId: json['user_id'],
          ));
          break;
          
        case 'error':
          print('Error: ${json['message']}');
          break;
      }
    } catch (e) {
      print('Parse error: $e');
    }
  }
  
  void _onError(error) {
    print('WebSocket error: $error');
    _attemptReconnect();
  }
  
  void _onDone() {
    print('WebSocket closed');
    if (_shouldReconnect) {
      _attemptReconnect();
    }
  }
  
  void _attemptReconnect() {
    _reconnectAttempts++;
    
    if (_reconnectAttempts >= _maxReconnectAttempts) {
      print('Max reconnection attempts reached');
      return;
    }
    
    final delay = Duration(seconds: _reconnectAttempts * 2);
    print('Reconnecting in ${delay.inSeconds}s... (Attempt $_reconnectAttempts)');
    
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(delay, () {
      connect();
    });
  }
  
  // Send text message
  void sendMessage(String message) {
    _send({
      'type': 'chat_message',
      'message': message,
      'message_type': 'text',
    });
  }
  
  // Send typing indicator
  void sendTypingIndicator(bool isTyping) {
    _send({
      'type': 'typing',
      'is_typing': isTyping,
    });
  }
  
  // Send read receipt
  void sendReadReceipt(int messageId) {
    _send({
      'type': 'read_receipt',
      'message_id': messageId,
    });
  }
  
  void _send(Map<String, dynamic> data) {
    try {
      _channel?.sink.add(jsonEncode(data));
    } catch (e) {
      print('Send error: $e');
    }
  }
  
  void dispose() {
    _shouldReconnect = false;
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _eventController?.close();
  }
}

// Events
abstract class ChatEvent {}

class ConnectionEstablished extends ChatEvent {}

class NewMessage extends ChatEvent {
  final int id;
  final int senderId;
  final String senderName;
  final String content;
  final String messageType;
  final DateTime createdAt;
  final bool isRead;
  
  NewMessage({
    required this.id,
    required this.senderId,
    required this.senderName,
    required this.content,
    required this.messageType,
    required this.createdAt,
    required this.isRead,
  });
}

class TypingIndicator extends ChatEvent {
  final int userId;
  final String userName;
  final bool isTyping;
  
  TypingIndicator({
    required this.userId,
    required this.userName,
    required this.isTyping,
  });
}

class ReadReceipt extends ChatEvent {
  final int messageId;
  final int userId;
  
  ReadReceipt({required this.messageId, required this.userId});
}
```

### 3. Chat Screen with WebSocket

```dart
class ChatScreen extends StatefulWidget {
  final int chatId;
  final int currentUserId;
  
  const ChatScreen({
    required this.chatId,
    required this.currentUserId,
  });
  
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  late ChatWebSocketService _ws;
  final TextEditingController _messageController = TextEditingController();
  final List<Message> _messages = [];
  
  String? _typingUserName;
  Timer? _typingTimer;
  
  @override
  void initState() {
    super.initState();
    _initWebSocket();
    _loadMessages();
  }
  
  Future<void> _initWebSocket() async {
    final token = await storage.read(key: 'access_token');
    
    _ws = ChatWebSocketService(
      chatId: widget.chatId,
      accessToken: token!,
    );
    
    _ws.events.listen((event) {
      if (event is ConnectionEstablished) {
        print('Connected!');
      } else if (event is NewMessage) {
        setState(() {
          _messages.add(Message(
            id: event.id,
            senderId: event.senderId,
            senderName: event.senderName,
            messageType: event.messageType,
            content: event.content,
            createdAt: event.createdAt,
            isRead: event.isRead,
          ));
        });
        
        // Send read receipt if not my message
        if (event.senderId != widget.currentUserId) {
          _ws.sendReadReceipt(event.id);
        }
      } else if (event is TypingIndicator) {
        if (event.userId != widget.currentUserId) {
          setState(() {
            _typingUserName = event.isTyping ? event.userName : null;
          });
        }
      } else if (event is ReadReceipt) {
        setState(() {
          final index = _messages.indexWhere((m) => m.id == event.messageId);
          if (index != -1) {
            _messages[index] = Message(
              id: _messages[index].id,
              senderId: _messages[index].senderId,
              senderName: _messages[index].senderName,
              messageType: _messages[index].messageType,
              content: _messages[index].content,
              createdAt: _messages[index].createdAt,
              isRead: true,
              readAt: DateTime.now(),
            );
          }
        });
      }
    });
    
    _ws.connect();
  }
  
  Future<void> _loadMessages() async {
    // Load initial messages from REST API
    final chatService = ChatService(...);
    final data = await chatService.getChatDetail(widget.chatId);
    
    if (data != null) {
      setState(() {
        _messages.addAll(data['messages']);
      });
    }
  }
  
  @override
  void dispose() {
    _ws.dispose();
    _typingTimer?.cancel();
    _messageController.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Chat'),
            if (_typingUserName != null)
              Text(
                '$_typingUserName is typing...',
                style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic),
              ),
          ],
        ),
      ),
      body: Column(
        children: [
          // Messages list
          Expanded(
            child: ListView.builder(
              reverse: true,
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[_messages.length - 1 - index];
                final isMe = message.senderId == widget.currentUserId;
                
                return MessageBubble(
                  message: message,
                  isMe: isMe,
                );
              },
            ),
          ),
          
          // Message input
          Container(
            padding: EdgeInsets.all(8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: InputDecoration(
                      hintText: 'Type a message',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                      ),
                    ),
                    onChanged: _onTyping,
                  ),
                ),
                SizedBox(width: 8),
                IconButton(
                  icon: Icon(Icons.send),
                  onPressed: _sendMessage,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  void _onTyping(String text) {
    // Send typing indicator
    _ws.sendTypingIndicator(true);
    
    // Stop typing after 2 seconds
    _typingTimer?.cancel();
    _typingTimer = Timer(Duration(seconds: 2), () {
      _ws.sendTypingIndicator(false);
    });
  }
  
  void _sendMessage() {
    if (_messageController.text.trim().isEmpty) return;
    
    final text = _messageController.text.trim();
    _messageController.clear();
    
    // Send via WebSocket
    _ws.sendMessage(text);
    _ws.sendTypingIndicator(false);
  }
}
```

---

## 📊 Message Format

### 1. Send Message
```json
{
  "type": "chat_message",
  "message": "Hello!",
  "message_type": "text"
}
```

### 2. Receive Message
```json
{
  "type": "chat_message",
  "message": {
    "id": 123,
    "sender_id": 5,
    "sender_name": "John Doe",
    "content": "Hello!",
    "message_type": "text",
    "created_at": "2025-10-06T12:34:56.789Z",
    "is_read": false
  }
}
```

### 3. Typing Indicator
```json
// Send
{
  "type": "typing",
  "is_typing": true
}

// Receive
{
  "type": "typing_indicator",
  "user_id": 5,
  "user_name": "John Doe",
  "is_typing": true
}
```

### 4. Read Receipt
```json
// Send
{
  "type": "read_receipt",
  "message_id": 123
}

// Receive
{
  "type": "read_receipt",
  "message_id": 123,
  "user_id": 5
}
```

---

## 🔒 Authentication

### JWT Token in URL
```dart
final uri = Uri.parse('ws://localhost:8000/ws/chat/1/?token=$accessToken');
```

### Error Codes
- **4001**: Unauthorized (invalid token)
- **4003**: Forbidden (not a chat participant)
- **1000**: Normal closure

---

## 🧪 Testing

### Browser Console
```javascript
const token = 'your_access_token';
const ws = new WebSocket(`ws://localhost:8000/ws/chat/1/?token=${token}`);

ws.onopen = () => {
  console.log('Connected!');
  
  // Send message
  ws.send(JSON.stringify({
    type: 'chat_message',
    message: 'Hello!',
    message_type: 'text'
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

### Postman
1. Create new WebSocket request
2. URL: `ws://localhost:8000/ws/chat/1/?token=YOUR_TOKEN`
3. Click Connect
4. Send messages

---

## 🎯 Best Practices

### 1. Auto-Reconnection
```dart
// Implemented in ChatWebSocketService
// Automatically reconnects with exponential backoff
```

### 2. Typing Indicator Debouncing
```dart
Timer? _typingTimer;

void _onTyping(String text) {
  _ws.sendTypingIndicator(true);
  
  _typingTimer?.cancel();
  _typingTimer = Timer(Duration(seconds: 2), () {
    _ws.sendTypingIndicator(false);
  });
}
```

### 3. Message Persistence
```dart
// Always load initial messages from REST API
// Use WebSocket for real-time updates only
Future<void> _loadMessages() async {
  final messages = await chatService.getMessages(chatId);
  setState(() => _messages.addAll(messages));
}
```

### 4. Read Receipts
```dart
// Send read receipt when message is received
if (event.senderId != currentUserId) {
  _ws.sendReadReceipt(event.id);
}
```

### 5. Connection Status
```dart
// Show connection indicator
class _ChatScreenState extends State<ChatScreen> {
  bool _isConnected = false;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          children: [
            Text('Chat'),
            if (!_isConnected)
              Text('Connecting...', style: TextStyle(fontSize: 12)),
          ],
        ),
      ),
      ...
    );
  }
}
```

---

## ⚠️ Troubleshooting

### WebSocket Connection Failed
- ✅ Check if Redis is running: `redis-cli ping`
- ✅ Verify JWT token is valid
- ✅ Ensure user is part of chat
- ✅ Check server is running on correct port

### Messages Not Received
- ✅ Check WebSocket connection status
- ✅ Verify event listener is set up
- ✅ Check browser/Flutter console for errors

### Typing Indicator Not Working
- ✅ Ensure debouncing is implemented
- ✅ Check both users are in same chat
- ✅ Verify WebSocket connection

---

## 🚀 Production Setup

### 1. Use WSS (Secure WebSocket)
```dart
const baseUrl = 'wss://yourdomain.com';
```

### 2. Nginx Configuration
```nginx
location /ws/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 86400;
}
```

### 3. Redis Configuration
```env
# Use Redis Cloud or hosted Redis
REDIS_URL=redis://user:password@redis-host:6379
```

---

## 📚 Summary

| Feature | Implementation |
|---------|---------------|
| Connect | `ws://localhost:8000/ws/chat/{id}/?token=xxx` |
| Send Message | `{'type': 'chat_message', 'message': '...'}` |
| Typing | `{'type': 'typing', 'is_typing': true}` |
| Read Receipt | `{'type': 'read_receipt', 'message_id': 123}` |
| Auto-Reconnect | Exponential backoff (2s, 4s, 6s...) |
| Authentication | JWT token in URL parameter |

---

For REST API, see **CHAT_SYSTEM.md**

For authentication, see **API_FLOW.md**
