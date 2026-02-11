import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

import '../config/brand_theme.dart';
import '../services/api_service.dart';
import '../models/chat.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;
  List<String> _suggestedCommands = ['Pomoč', 'Preveri emaile', 'Seznam projektov'];

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _sendMessage([String? quickCommand]) async {
    final message = quickCommand ?? _messageController.text.trim();
    if (message.isEmpty) return;

    setState(() {
      _messages.add(ChatMessage(
        role: 'user',
        content: message,
        timestamp: DateTime.now(),
      ));
      _isLoading = true;
    });

    _messageController.clear();
    _scrollToBottom();

    try {
      final apiService = context.read<ApiService>();
      final response = await apiService.sendMessage(message);

      setState(() {
        _messages.add(response);
        _isLoading = false;
        if (response.suggestedCommands != null) {
          _suggestedCommands = response.suggestedCommands!;
        }
      });

      _scrollToBottom();
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(
          role: 'system',
          content: 'Napaka: Ne morem se povezati s strežnikom.',
          timestamp: DateTime.now(),
        ));
        _isLoading = false;
      });
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: LuznarBrand.surface,
      child: Column(
        children: [
          // Messages
          Expanded(
            child: _messages.isEmpty
                ? _buildWelcome()
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    itemCount: _messages.length + (_isLoading ? 1 : 0),
                    itemBuilder: (context, index) {
                      if (_isLoading && index == _messages.length) {
                        return _buildTypingIndicator();
                      }
                      return _buildMessageBubble(_messages[index]);
                    },
                  ),
          ),

          // Suggested commands
          if (_suggestedCommands.isNotEmpty)
            Container(
              height: 44,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: _suggestedCommands.length,
                itemBuilder: (context, index) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3, vertical: 6),
                    child: ActionChip(
                      label: Text(
                        _suggestedCommands[index],
                        style: const TextStyle(
                          fontSize: 12,
                          color: LuznarBrand.navy,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      backgroundColor: LuznarBrand.surfaceWhite,
                      side: BorderSide(color: LuznarBrand.navy.withValues(alpha: 0.15)),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(LuznarBrand.radiusXLarge),
                      ),
                      onPressed: () => _sendMessage(_suggestedCommands[index]),
                    ),
                  );
                },
              ),
            ),

          // Message input
          Container(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
            decoration: BoxDecoration(
              color: LuznarBrand.surfaceWhite,
              border: Border(
                top: BorderSide(
                  color: LuznarBrand.navy.withValues(alpha: 0.06),
                ),
              ),
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      decoration: BoxDecoration(
                        color: LuznarBrand.surface,
                        borderRadius: BorderRadius.circular(LuznarBrand.radiusXLarge),
                        border: Border.all(
                          color: LuznarBrand.navy.withValues(alpha: 0.1),
                        ),
                      ),
                      child: TextField(
                        controller: _messageController,
                        decoration: InputDecoration(
                          hintText: 'Vprašajte karkoli o ERP...',
                          hintStyle: TextStyle(
                            color: LuznarBrand.textMuted,
                            fontSize: 14,
                          ),
                          border: InputBorder.none,
                          enabledBorder: InputBorder.none,
                          focusedBorder: InputBorder.none,
                          filled: false,
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 18,
                            vertical: 12,
                          ),
                        ),
                        style: const TextStyle(fontSize: 14),
                        textInputAction: TextInputAction.send,
                        onSubmitted: (_) => _sendMessage(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Material(
                    color: LuznarBrand.navy,
                    borderRadius: BorderRadius.circular(LuznarBrand.radiusXLarge),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(LuznarBrand.radiusXLarge),
                      onTap: _isLoading ? null : () => _sendMessage(),
                      child: Container(
                        width: 42,
                        height: 42,
                        alignment: Alignment.center,
                        child: Icon(
                          Icons.send_rounded,
                          color: _isLoading
                              ? Colors.white.withValues(alpha: 0.4)
                              : Colors.white,
                          size: 20,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWelcome() {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: LuznarBrand.navy.withValues(alpha: 0.06),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Center(
                child: LuznarLogo(
                  size: 48,
                  color: LuznarBrand.navy,
                ),
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'Dobrodošli',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w600,
                color: LuznarBrand.navy,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Kako vam lahko pomagam danes?',
              style: TextStyle(
                fontSize: 15,
                color: LuznarBrand.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            const GoldAccentLine(width: 32),
            const SizedBox(height: 32),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              alignment: WrapAlignment.center,
              children: [
                _buildQuickAction('Preveri emaile', Icons.email_outlined),
                _buildQuickAction('Seznam projektov', Icons.folder_outlined),
                _buildQuickAction('Nov projekt', Icons.add_circle_outline),
                _buildQuickAction('Pomoč', Icons.help_outline),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickAction(String label, IconData icon) {
    return Material(
      color: LuznarBrand.surfaceWhite,
      borderRadius: BorderRadius.circular(LuznarBrand.radiusMedium),
      child: InkWell(
        borderRadius: BorderRadius.circular(LuznarBrand.radiusMedium),
        onTap: () => _sendMessage(label),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(LuznarBrand.radiusMedium),
            border: Border.all(
              color: LuznarBrand.navy.withValues(alpha: 0.1),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 18, color: LuznarBrand.gold),
              const SizedBox(width: 8),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: LuznarBrand.navy,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    final isUser = message.isUser;
    final isSystem = message.isSystem;

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: isSystem
                    ? LuznarBrand.warning.withValues(alpha: 0.1)
                    : LuznarBrand.navy,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Center(
                child: isSystem
                    ? Icon(Icons.info_outline, size: 16,
                        color: LuznarBrand.warning)
                    : const LuznarLogo(size: 18, color: LuznarBrand.gold),
              ),
            ),
            const SizedBox(width: 10),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isUser
                    ? LuznarBrand.navy
                    : isSystem
                        ? LuznarBrand.warning.withValues(alpha: 0.06)
                        : LuznarBrand.surfaceWhite,
                borderRadius: BorderRadius.circular(LuznarBrand.radiusMedium).copyWith(
                  topLeft: isUser ? null : const Radius.circular(4),
                  topRight: isUser ? const Radius.circular(4) : null,
                ),
                border: isUser
                    ? null
                    : Border.all(
                        color: isSystem
                            ? LuznarBrand.warning.withValues(alpha: 0.15)
                            : LuznarBrand.navy.withValues(alpha: 0.06),
                      ),
                boxShadow: isUser ? null : LuznarBrand.shadowSmall,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (isUser)
                    Text(
                      message.content,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        height: 1.4,
                      ),
                    )
                  else
                    MarkdownBody(
                      data: message.content,
                      selectable: true,
                      styleSheet: MarkdownStyleSheet(
                        p: const TextStyle(
                          color: LuznarBrand.textPrimary,
                          fontSize: 14,
                          height: 1.5,
                        ),
                        tableHead: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                          color: LuznarBrand.navy,
                        ),
                        tableBody: const TextStyle(
                          fontSize: 13,
                          color: LuznarBrand.textPrimary,
                        ),
                        tableBorder: TableBorder.all(
                          color: LuznarBrand.navy.withValues(alpha: 0.12),
                          width: 0.5,
                        ),
                        tableCellsPadding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 5,
                        ),
                        code: TextStyle(
                          backgroundColor: LuznarBrand.surface,
                          fontSize: 13,
                          fontFamily: 'monospace',
                          color: LuznarBrand.navy,
                        ),
                        codeblockDecoration: BoxDecoration(
                          color: LuznarBrand.surface,
                          borderRadius: BorderRadius.circular(LuznarBrand.radiusSmall),
                          border: Border.all(
                            color: LuznarBrand.navy.withValues(alpha: 0.08),
                          ),
                        ),
                        strong: const TextStyle(
                          fontWeight: FontWeight.w600,
                          color: LuznarBrand.navy,
                        ),
                        h1: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: LuznarBrand.navy,
                        ),
                        h2: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: LuznarBrand.navy,
                        ),
                        h3: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: LuznarBrand.navy,
                        ),
                      ),
                    ),
                  // Pending actions buttons
                  if (message.needsConfirmation && message.actions != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 10),
                      child: Column(
                        children: message.actions!.map((action) {
                          return _buildActionButtons(action);
                        }).toList(),
                      ),
                    ),
                  const SizedBox(height: 6),
                  Text(
                    DateFormat('HH:mm').format(message.timestamp),
                    style: TextStyle(
                      fontSize: 10,
                      color: isUser
                          ? Colors.white.withValues(alpha: 0.5)
                          : LuznarBrand.textMuted,
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (isUser) ...[
            const SizedBox(width: 10),
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: LuznarBrand.gold.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Center(
                child: Icon(Icons.person, size: 18, color: LuznarBrand.gold),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildActionButtons(Map<String, dynamic> action) {
    final status = action['status'] ?? 'Čaka';
    final description = action['description'] ?? action['tool_name'] ?? '';
    final actionId = action['id'] ?? '';

    if (status != 'Čaka') {
      final isConfirmed = status == 'Potrjeno';
      return Container(
        margin: const EdgeInsets.only(bottom: 6),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: isConfirmed
              ? LuznarBrand.success.withValues(alpha: 0.06)
              : LuznarBrand.error.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(LuznarBrand.radiusSmall),
          border: Border.all(
            color: isConfirmed
                ? LuznarBrand.success.withValues(alpha: 0.2)
                : LuznarBrand.error.withValues(alpha: 0.2),
          ),
        ),
        child: Row(
          children: [
            Icon(
              isConfirmed ? Icons.check_circle_outline : Icons.cancel_outlined,
              size: 16,
              color: isConfirmed ? LuznarBrand.success : LuznarBrand.error,
            ),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                '$description - $status',
                style: TextStyle(
                  fontSize: 12,
                  color: isConfirmed ? LuznarBrand.success : LuznarBrand.error,
                ),
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: LuznarBrand.warning.withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(LuznarBrand.radiusSmall),
        border: Border.all(
          color: LuznarBrand.warning.withValues(alpha: 0.2),
        ),
      ),
      child: Row(
        children: [
          Icon(Icons.pending_actions, size: 18, color: LuznarBrand.gold),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              description,
              style: const TextStyle(
                fontSize: 13,
                color: LuznarBrand.textPrimary,
              ),
            ),
          ),
          const SizedBox(width: 4),
          SizedBox(
            height: 30,
            child: TextButton(
              onPressed: () => _confirmAction(actionId),
              style: TextButton.styleFrom(
                foregroundColor: LuznarBrand.success,
                padding: const EdgeInsets.symmetric(horizontal: 10),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(LuznarBrand.radiusSmall),
                ),
              ),
              child: const Text('Potrdi', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            ),
          ),
          SizedBox(
            height: 30,
            child: TextButton(
              onPressed: () => _rejectAction(actionId),
              style: TextButton.styleFrom(
                foregroundColor: LuznarBrand.error,
                padding: const EdgeInsets.symmetric(horizontal: 10),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(LuznarBrand.radiusSmall),
                ),
              ),
              child: const Text('Zavrni', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _confirmAction(String actionId) async {
    if (actionId.isEmpty) return;
    try {
      final apiService = context.read<ApiService>();
      await apiService.confirmAction(actionId);
      setState(() {
        for (final msg in _messages) {
          if (msg.actions != null) {
            for (final action in msg.actions!) {
              if (action['id'] == actionId) {
                action['status'] = 'Potrjeno';
              }
            }
          }
        }
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Napaka: $e')),
        );
      }
    }
  }

  Future<void> _rejectAction(String actionId) async {
    if (actionId.isEmpty) return;
    try {
      final apiService = context.read<ApiService>();
      await apiService.rejectAction(actionId);
      setState(() {
        for (final msg in _messages) {
          if (msg.actions != null) {
            for (final action in msg.actions!) {
              if (action['id'] == actionId) {
                action['status'] = 'Zavrnjeno';
              }
            }
          }
        }
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Napaka: $e')),
        );
      }
    }
  }

  Widget _buildTypingIndicator() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: LuznarBrand.navy,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Center(
              child: LuznarLogo(size: 18, color: LuznarBrand.gold),
            ),
          ),
          const SizedBox(width: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: LuznarBrand.surfaceWhite,
              borderRadius: BorderRadius.circular(LuznarBrand.radiusMedium).copyWith(
                topLeft: const Radius.circular(4),
              ),
              border: Border.all(
                color: LuznarBrand.navy.withValues(alpha: 0.06),
              ),
              boxShadow: LuznarBrand.shadowSmall,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _TypingDot(delay: 0),
                _TypingDot(delay: 1),
                _TypingDot(delay: 2),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TypingDot extends StatefulWidget {
  final int delay;
  const _TypingDot({required this.delay});

  @override
  State<_TypingDot> createState() => _TypingDotState();
}

class _TypingDotState extends State<_TypingDot>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _animation = Tween<double>(begin: 0.3, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    Future.delayed(Duration(milliseconds: widget.delay * 200), () {
      if (mounted) {
        _controller.repeat(reverse: true);
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 2),
          width: 7,
          height: 7,
          decoration: BoxDecoration(
            color: LuznarBrand.gold.withValues(alpha: _animation.value),
            shape: BoxShape.circle,
          ),
        );
      },
    );
  }
}
