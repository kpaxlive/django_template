# 💬 Chat System - REST API

Complete REST API guide for chat functionality with Flutter examples.

---

## 📋 Overview

The chat system provides:
- One-on-one messaging
- Text, image, file messages
- Read receipts
- Message deletion (for me / everyone)
- Per-user message clearing
- Chat archiving
- Unread counts

**Feature is OPTIONAL** - Enable via `.env`:
```env
ENABLE_CHAT_SYSTEM=True
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/chat/` | List user's chats |
| `POST` | `/api/chat/create/` | Create new chat |
| `GET` | `/api/chat/{id}/` | Get chat details |
| `DELETE` | `/api/chat/{id}/` | Delete chat (for me) |
| `POST` | `/api/chat/{id}/archive/` | Archive chat |
| `DELETE` | `/api/chat/{id}/archive/` | Unarchive chat |
| `GET` | `/api/chat/{id}/messages/` | Get messages |
| `POST` | `/api/chat/{id}/messages/send/` | Send message |
| `POST` | `/api/chat/{id}/messages/read/` | Mark as read |
| `POST` | `/api/chat/{id}/messages/clear/` | Clear all messages |
| `DELETE` | `/api/chat/messages/{id}/delete/` | Delete message |

---

## 📱 Flutter Models

```dart
// models/user.dart
class User {
  final int id;
  final String email;
  final String firstName;
  final String lastName;
  final String? profilePictureUrl;
  final String? bio;
  
  User({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    this.profilePictureUrl,
    this.bio,
  });
  
  factory User.fromJson(Map<String, dynamic> json) => User(
    id: json['id'],
    email: json['email'],
    firstName: json['first_name'],
    lastName: json['last_name'],
    profilePictureUrl: json['profile_picture_url'],
    bio: json['bio'],
  );
  
  String get fullName => '$firstName $lastName'.trim();
}

// models/message.dart
class Message {
  final int id;
  final int senderId;
  final String senderName;
  final String messageType; // 'text', 'image', 'file'
  final String? content;
  final String? image;
  final String? file;
  final DateTime createdAt;
  final bool isRead;
  final DateTime? readAt;
  
  Message({
    required this.id,
    required this.senderId,
    required this.senderName,
    required this.messageType,
    this.content,
    this.image,
    this.file,
    required this.createdAt,
    required this.isRead,
    this.readAt,
  });
  
  factory Message.fromJson(Map<String, dynamic> json) => Message(
    id: json['id'],
    senderId: json['sender'],
    senderName: json['sender_name'],
    messageType: json['message_type'],
    content: json['content'],
    image: json['image'],
    file: json['file'],
    createdAt: DateTime.parse(json['created_at']),
    isRead: json['is_read'],
    readAt: json['read_at'] != null ? DateTime.parse(json['read_at']) : null,
  );
}

// models/chat.dart
class Chat {
  final int id;
  final User otherParticipant;
  final Message? lastMessage;
  final int unreadCount;
  final DateTime createdAt;
  final DateTime updatedAt;
  
  Chat({
    required this.id,
    required this.otherParticipant,
    this.lastMessage,
    required this.unreadCount,
    required this.createdAt,
    required this.updatedAt,
  });
  
  factory Chat.fromJson(Map<String, dynamic> json) => Chat(
    id: json['id'],
    otherParticipant: User.fromJson(json['other_participant']),
    lastMessage: json['last_message'] != null
        ? Message.fromJson(json['last_message'])
        : null,
    unreadCount: json['unread_count'],
    createdAt: DateTime.parse(json['created_at']),
    updatedAt: DateTime.parse(json['updated_at']),
  );
}
```

---

## 🎯 Chat Service

```dart
// services/chat_service.dart
import 'package:dio/dio.dart';

class ChatService {
  final Dio dio;
  final String Function() getToken; // Get access token
  
  ChatService({required this.dio, required this.getToken});
  
  // Get chat list
  Future<List<Chat>> getChatList() async {
    final response = await dio.get(
      '/chat/',
      options: Options(headers: {
        'Authorization': 'Bearer ${getToken()}',
      }),
    );
    
    if (response.data['success']) {
      return (response.data['data'] as List)
          .map((json) => Chat.fromJson(json))
          .toList();
    }
    
    return [];
  }
  
  // Create chat
  Future<Chat?> createChat(int otherUserId) async {
    final response = await dio.post(
      '/chat/create/',
      data: {'other_user_id': otherUserId},
      options: Options(headers: {
        'Authorization': 'Bearer ${getToken()}',
      }),
    );
    
    if (response.data['success']) {
      return Chat.fromJson(response.data['data']);
    }
    
    return null;
  }
  
  // Get chat details
  Future<Map<String, dynamic>?> getChatDetail(int chatId) async {
    final response = await dio.get(
      '/chat/$chatId/',
      options: Options(headers: {
        'Authorization': 'Bearer ${getToken()}',
      }),
    );
    
    if (response.data['success']) {
      return {
        'chat': Chat.fromJson(response.data['data']['chat']),
        'messages': (response.data['data']['messages'] as List)
            .map((json) => Message.fromJson(json))
            .toList(),
      };
    }
    
    return null;
  }
  
  // Send text message
  Future<Message?> sendMessage({
    required int chatId,
    required String message,
  }) async {
    final response = await dio.post(
      '/chat/$chatId/messages/send/',
      data: {
        'message_type': 'text',
        'content': message,
      },
      options: Options(headers: {
        'Authorization': 'Bearer ${getToken()}',
      }),
    );
    
    if (response.data['success']) {
      return Message.fromJson(response.data['data']);
    }
    
    return null;
  }
  
  // Send image
  Future<Message?> sendImage({
    required int chatId,
    required String imagePath,
  }) async {
    final formData = FormData.fromMap({
      'message_type': 'image',
      'image': await MultipartFile.fromFile(imagePath),
    });
    
    final response = await dio.post(
      '/chat/$chatId/messages/send/',
      data: formData,
      options: Options(headers: {
        'Authorization': 'Bearer ${getToken()}',
      }),
    );
    
    if (response.data['success']) {
      return Message.fromJson(response.data['data']);
    }
    
    return null;
  }
  
  // Mark messages as read
  Future<bool> markAsRead(int chatId) async {
    final response = await dio.post(
      '/chat/$chatId/messages/read/',
      options: Options(headers: {
        'Authorization': 'Bearer ${getToken()}',
      }),
    );
    
    return response.data['success'] ?? false;
  }
  
  // Delete message
  Future<bool> deleteMessage({
    required int messageId,
    required bool deleteForEveryone,
  }) async {
    final response = await dio.delete(
      '/chat/messages/$messageId/delete/',
      data: {'delete_for_everyone': deleteForEveryone},
      options: Options(headers: {
        'Authorization': 'Bearer ${getToken()}',
      }),
    );
    
    return response.data['success'] ?? false;
  }
  
  // Clear messages
  Future<bool> clearMessages(int chatId) async {
    final response = await dio.post(
      '/chat/$chatId/messages/clear/',
      options: Options(headers: {
        'Authorization': 'Bearer ${getToken()}',
      }),
    );
    
    return response.data['success'] ?? false;
  }
  
  // Archive chat
  Future<bool> archiveChat(int chatId) async {
    final response = await dio.post(
      '/chat/$chatId/archive/',
      options: Options(headers: {
        'Authorization': 'Bearer ${getToken()}',
      }),
    );
    
    return response.data['success'] ?? false;
  }
  
  // Unarchive chat
  Future<bool> unarchiveChat(int chatId) async {
    final response = await dio.delete(
      '/chat/$chatId/archive/',
      options: Options(headers: {
        'Authorization': 'Bearer ${getToken()}',
      }),
    );
    
    return response.data['success'] ?? false;
  }
  
  // Delete chat
  Future<bool> deleteChat(int chatId) async {
    final response = await dio.delete(
      '/chat/$chatId/',
      options: Options(headers: {
        'Authorization': 'Bearer ${getToken()}',
      }),
    );
    
    return response.data['success'] ?? false;
  }
}
```

---

## 🎨 UI Implementation

### 1. Chat List Screen

```dart
class ChatListScreen extends StatefulWidget {
  @override
  State<ChatListScreen> createState() => _ChatListScreenState();
}

class _ChatListScreenState extends State<ChatListScreen> {
  final ChatService _chatService = ChatService(
    dio: dio,
    getToken: () => storage.read(key: 'access_token'),
  );
  
  List<Chat> _chats = [];
  bool _loading = true;
  
  @override
  void initState() {
    super.initState();
    _loadChats();
  }
  
  Future<void> _loadChats() async {
    setState(() => _loading = true);
    _chats = await _chatService.getChatList();
    setState(() => _loading = false);
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Chats')),
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: _chats.length,
              itemBuilder: (context, index) {
                final chat = _chats[index];
                return ListTile(
                  leading: CircleAvatar(
                    backgroundImage: chat.otherParticipant.profilePictureUrl != null
                        ? NetworkImage(chat.otherParticipant.profilePictureUrl!)
                        : null,
                    child: chat.otherParticipant.profilePictureUrl == null
                        ? Text(chat.otherParticipant.firstName[0])
                        : null,
                  ),
                  title: Text(chat.otherParticipant.fullName),
                  subtitle: Text(
                    chat.lastMessage?.content ?? 'No messages yet',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  trailing: chat.unreadCount > 0
                      ? Container(
                          padding: EdgeInsets.all(6),
                          decoration: BoxDecoration(
                            color: Colors.blue,
                            shape: BoxShape.circle,
                          ),
                          child: Text(
                            '${chat.unreadCount}',
                            style: TextStyle(color: Colors.white, fontSize: 12),
                          ),
                        )
                      : null,
                  onTap: () => _openChat(chat),
                );
              },
            ),
    );
  }
  
  void _openChat(Chat chat) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ChatDetailScreen(chatId: chat.id),
      ),
    ).then((_) => _loadChats()); // Reload on return
  }
}
```

### 2. Chat Detail Screen

```dart
class ChatDetailScreen extends StatefulWidget {
  final int chatId;
  
  const ChatDetailScreen({required this.chatId});
  
  @override
  State<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends State<ChatDetailScreen> {
  final ChatService _chatService = ChatService(...);
  final TextEditingController _messageController = TextEditingController();
  
  Chat? _chat;
  List<Message> _messages = [];
  bool _loading = true;
  
  @override
  void initState() {
    super.initState();
    _loadChat();
  }
  
  Future<void> _loadChat() async {
    setState(() => _loading = true);
    
    final data = await _chatService.getChatDetail(widget.chatId);
    
    if (data != null) {
      setState(() {
        _chat = data['chat'];
        _messages = data['messages'];
      });
      
      // Mark as read
      await _chatService.markAsRead(widget.chatId);
    }
    
    setState(() => _loading = false);
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_chat?.otherParticipant.fullName ?? 'Chat'),
        actions: [
          PopupMenuButton(
            itemBuilder: (context) => [
              PopupMenuItem(
                value: 'clear',
                child: Text('Clear messages'),
              ),
              PopupMenuItem(
                value: 'archive',
                child: Text('Archive chat'),
              ),
              PopupMenuItem(
                value: 'delete',
                child: Text('Delete chat'),
              ),
            ],
            onSelected: _handleMenuAction,
          ),
        ],
      ),
      body: Column(
        children: [
          // Messages list
          Expanded(
            child: _loading
                ? Center(child: CircularProgressIndicator())
                : ListView.builder(
                    reverse: true,
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final message = _messages[_messages.length - 1 - index];
                      final isMe = message.senderId == currentUserId;
                      
                      return MessageBubble(
                        message: message,
                        isMe: isMe,
                        onLongPress: () => _showMessageOptions(message, isMe),
                      );
                    },
                  ),
          ),
          
          // Message input
          Container(
            padding: EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4)],
            ),
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
  
  Future<void> _sendMessage() async {
    if (_messageController.text.trim().isEmpty) return;
    
    final text = _messageController.text.trim();
    _messageController.clear();
    
    final message = await _chatService.sendMessage(
      chatId: widget.chatId,
      message: text,
    );
    
    if (message != null) {
      setState(() {
        _messages.insert(0, message);
      });
    }
  }
  
  void _showMessageOptions(Message message, bool isMe) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (isMe)
            ListTile(
              leading: Icon(Icons.delete_forever),
              title: Text('Delete for everyone'),
              onTap: () {
                Navigator.pop(context);
                _deleteMessage(message.id, deleteForEveryone: true);
              },
            ),
          ListTile(
            leading: Icon(Icons.delete),
            title: Text('Delete for me'),
            onTap: () {
              Navigator.pop(context);
              _deleteMessage(message.id, deleteForEveryone: false);
            },
          ),
        ],
      ),
    );
  }
  
  Future<void> _deleteMessage(int messageId, {required bool deleteForEveryone}) async {
    final success = await _chatService.deleteMessage(
      messageId: messageId,
      deleteForEveryone: deleteForEveryone,
    );
    
    if (success) {
      setState(() {
        _messages.removeWhere((m) => m.id == messageId);
      });
    }
  }
  
  Future<void> _handleMenuAction(String action) async {
    switch (action) {
      case 'clear':
        await _chatService.clearMessages(widget.chatId);
        setState(() => _messages.clear());
        break;
      case 'archive':
        await _chatService.archiveChat(widget.chatId);
        Navigator.pop(context);
        break;
      case 'delete':
        await _chatService.deleteChat(widget.chatId);
        Navigator.pop(context);
        break;
    }
  }
}

// Message Bubble Widget
class MessageBubble extends StatelessWidget {
  final Message message;
  final bool isMe;
  final VoidCallback onLongPress;
  
  const MessageBubble({
    required this.message,
    required this.isMe,
    required this.onLongPress,
  });
  
  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: GestureDetector(
        onLongPress: onLongPress,
        child: Container(
          margin: EdgeInsets.symmetric(vertical: 4, horizontal: 8),
          padding: EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: isMe ? Colors.blue : Colors.grey[300],
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (message.messageType == 'text')
                Text(
                  message.content ?? '',
                  style: TextStyle(
                    color: isMe ? Colors.white : Colors.black,
                  ),
                )
              else if (message.messageType == 'image')
                Image.network(message.image!),
              
              SizedBox(height: 4),
              
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    _formatTime(message.createdAt),
                    style: TextStyle(
                      fontSize: 10,
                      color: isMe ? Colors.white70 : Colors.black54,
                    ),
                  ),
                  if (isMe && message.isRead) ...[
                    SizedBox(width: 4),
                    Icon(Icons.done_all, size: 14, color: Colors.white70),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  String _formatTime(DateTime time) {
    return '${time.hour}:${time.minute.toString().padLeft(2, '0')}';
  }
}
```

---

## 📚 API Response Examples

### Get Chat List
```json
{
  "success": true,
  "code": "SUCCESS",
  "data": [
    {
      "id": 1,
      "other_participant": {
        "id": 2,
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "profile_picture_url": "https://example.com/john.jpg"
      },
      "last_message": {
        "id": 10,
        "content": "Hello!",
        "created_at": "2025-10-06T12:34:56.789Z"
      },
      "unread_count": 3
    }
  ]
}
```

### Send Message
```json
{
  "success": true,
  "code": "CREATED",
  "message": "Message sent successfully.",
  "data": {
    "id": 11,
    "sender": 1,
    "sender_name": "Me",
    "message_type": "text",
    "content": "Hi there!",
    "created_at": "2025-10-06T12:35:00.000Z",
    "is_read": false
  }
}
```

---

## 🎯 Key Features

### 1. Per-User Message Clearing
- User A clears messages → Only A's messages hidden
- User B still sees all messages
- New messages appear for both

### 2. Message Deletion
- **Delete for me**: Only I can't see it
- **Delete for everyone**: No one can see it (only sender)

### 3. Unread Counts
- Automatically updated
- Respects message clearing
- Reset when chat is opened

### 4. Chat Archiving
- Hide chat from list
- Unarchive anytime
- Per-user (doesn't affect other person)

---

For real-time messaging, see **WEBSOCKET_CHAT.md**

For authentication, see **API_FLOW.md**
