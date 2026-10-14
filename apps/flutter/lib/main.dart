import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import 'api.dart';
import 'models.dart';
import 'theme.dart';

final api = TruthLensApi();

void main() {
  runApp(const TruthLensApp());
}

class TruthLensApp extends StatelessWidget {
  const TruthLensApp({super.key});

  @override
  Widget build(BuildContext context) {
    final router = GoRouter(
      initialLocation: '/splash',
      routes: [
        GoRoute(path: '/splash', builder: (_, __) => const SplashScreen()),
        GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
        GoRoute(
          path: '/processing/:id',
          builder: (_, state) => ProcessingScreen(id: state.pathParameters['id']!),
        ),
        GoRoute(
          path: '/result/:id',
          builder: (_, state) => ResultScreen(id: state.pathParameters['id']!),
        ),
        GoRoute(path: '/history', builder: (_, __) => const HistoryScreen()),
        GoRoute(path: '/analytics', builder: (_, __) => const AnalyticsScreen()),
      ],
    );
    return MaterialApp.router(title: 'TruthLens', theme: truthTheme(), routerConfig: router);
  }
}

class Shell extends StatelessWidget {
  const Shell({super.key, required this.child, required this.active});
  final Widget child;
  final String active;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
            decoration: BoxDecoration(
              color: TruthColors.panel,
              border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.08))),
            ),
            child: Row(
              children: [
                Text('TRUTH', style: GoogleFonts.inter(fontWeight: FontWeight.w700, letterSpacing: 3)),
                Text('LENS', style: GoogleFonts.inter(fontWeight: FontWeight.w700, letterSpacing: 3, color: TruthColors.cyan)),
                const SizedBox(width: 12),
                Text('CORE V0.1', style: GoogleFonts.jetBrainsMono(fontSize: 10, color: TruthColors.cyan)),
                const Spacer(),
                _nav(context, 'HOME / VERIFY', '/', active == 'home'),
                _nav(context, 'HISTORY', '/history', active == 'history'),
                _nav(context, 'ANALYTICS', '/analytics', active == 'analytics'),
              ],
            ),
          ),
          Expanded(child: child),
        ],
      ),
    );
  }

  Widget _nav(BuildContext context, String label, String path, bool on) {
    return TextButton(
      onPressed: () => context.go(path),
      child: Text(
        label,
        style: GoogleFonts.jetBrainsMono(
          fontSize: 11,
          color: on ? TruthColors.cyan : TruthColors.muted,
        ),
      ),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    Future.delayed(const Duration(milliseconds: 1600), () {
      if (mounted) context.go('/');
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: TruthColors.voidBg,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: TruthColors.cyan.withOpacity(0.6), width: 2),
                boxShadow: const [BoxShadow(color: Color(0x5906B6D4), blurRadius: 24)],
              ),
              child: const Icon(Icons.center_focus_strong, color: TruthColors.cyan, size: 48),
            ),
            const SizedBox(height: 24),
            Text('TRUTHLENS', style: GoogleFonts.inter(fontSize: 36, fontWeight: FontWeight.w700, letterSpacing: 8)),
            const SizedBox(height: 8),
            Text('AGENTIC FACT VERIFICATION SYSTEM', style: GoogleFonts.jetBrainsMono(fontSize: 12, color: TruthColors.muted, letterSpacing: 4)),
            const SizedBox(height: 24),
            Text('SYSTEM ONLINE // EVIDENCE ENGINE READY', style: GoogleFonts.jetBrainsMono(fontSize: 11, color: TruthColors.verdant)),
          ],
        ),
      ),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final controller = TextEditingController();
  String? error;
  bool busy = false;

  Future<void> _verify() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final created = await api.verifyClaim(controller.text);
      if (mounted) context.go('/processing/${created.id}');
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _upload() async {
    final picked = await FilePicker.platform.pickFiles(withData: true, type: FileType.image);
    if (picked == null || picked.files.single.bytes == null) return;
    setState(() => busy = true);
    try {
      final created = await api.verifyScreenshot(picked.files.single.bytes!, picked.files.single.name);
      if (mounted) context.go('/processing/${created.id}');
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Shell(
      active: 'home',
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('SEC_01 // CLAIM INTAKE', style: GoogleFonts.jetBrainsMono(color: TruthColors.cyan, fontSize: 12)),
                const SizedBox(height: 12),
                Text('Verify a claim', style: GoogleFonts.inter(fontSize: 32, fontWeight: FontWeight.w600)),
                const SizedBox(height: 8),
                Text('Submit a social, news, health, science, or political claim. TruthLens investigates; it does not chat.', style: GoogleFonts.inter(color: TruthColors.muted)),
                const SizedBox(height: 24),
                TextField(
                  controller: controller,
                  maxLines: 5,
                  style: GoogleFonts.inter(),
                  decoration: InputDecoration(
                    hintText: 'Enter the claim you want investigated',
                    hintStyle: GoogleFonts.jetBrainsMono(color: TruthColors.muted),
                    filled: true,
                    fillColor: TruthColors.voidBg,
                    enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white.withOpacity(0.12))),
                    focusedBorder: const OutlineInputBorder(borderSide: BorderSide(color: TruthColors.cyan, width: 1.4)),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    FilledButton(
                      onPressed: busy ? null : _verify,
                      style: FilledButton.styleFrom(backgroundColor: TruthColors.cyan, foregroundColor: TruthColors.voidBg),
                      child: Text(busy ? 'DISPATCHING…' : 'VERIFY', style: GoogleFonts.jetBrainsMono(fontWeight: FontWeight.w600)),
                    ),
                    const SizedBox(width: 12),
                    OutlinedButton(
                      onPressed: busy ? null : _upload,
                      style: OutlinedButton.styleFrom(foregroundColor: TruthColors.indigo, side: const BorderSide(color: Color(0x666366F1))),
                      child: Text('UPLOAD SCREENSHOT', style: GoogleFonts.jetBrainsMono()),
                    ),
                  ],
                ),
                if (error != null) ...[
                  const SizedBox(height: 12),
                  Text(error!, style: const TextStyle(color: TruthColors.crimson)),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class ProcessingScreen extends StatefulWidget {
  const ProcessingScreen({super.key, required this.id});
  final String id;
  @override
  State<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends State<ProcessingScreen> {
  final steps = <String>[];

  @override
  void initState() {
    super.initState();
    api.events(widget.id).listen((event) {
      setState(() => steps.add(event.message));
      if (event.type == 'completed' || event.type == 'failed') {
        Future.delayed(const Duration(milliseconds: 400), () {
          if (mounted) context.go('/result/${widget.id}');
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    const expected = [
      'Extracting Claim...',
      'Searching Fact Databases...',
      'Searching Evidence...',
      'Building Knowledge Graph...',
      'Evaluating Sources...',
      'Generating Verdict...',
    ];
    return Shell(
      active: 'home',
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('SEC_02 // LIVE INVESTIGATION', style: GoogleFonts.jetBrainsMono(color: TruthColors.cyan)),
            const SizedBox(height: 16),
            ...expected.map((label) {
              final done = steps.any((s) => s.contains(label.replaceAll('...', '')) || s == label);
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Row(
                  children: [
                    Icon(done ? Icons.check_circle : Icons.radio_button_unchecked, color: done ? TruthColors.cyan : TruthColors.muted, size: 18),
                    const SizedBox(width: 12),
                    Text(label, style: GoogleFonts.jetBrainsMono(color: done ? TruthColors.text : TruthColors.muted)),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class ResultScreen extends StatefulWidget {
  const ResultScreen({super.key, required this.id});
  final String id;
  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  Dossier? dossier;

  @override
  void initState() {
    super.initState();
    api.dossier(widget.id).then((value) => setState(() => dossier = value));
  }

  @override
  Widget build(BuildContext context) {
    final d = dossier;
    if (d == null) {
      return const Shell(active: 'home', child: Center(child: CircularProgressIndicator()));
    }
    final verdict = d.verdict;
    final label = verdict?['verdict'] as String? ?? 'UNVERIFIABLE';
    final confidence = ((verdict?['confidence'] as num?) ?? 0) * 100;
    final reasoning = (verdict?['reasoning'] as List<dynamic>?) ?? [];
    return Shell(
      active: 'home',
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('SEC_03 // FORENSIC DOSSIER', style: GoogleFonts.jetBrainsMono(color: TruthColors.cyan)),
            const SizedBox(height: 12),
            Text('“${d.original}”', style: GoogleFonts.inter(fontSize: 22, fontWeight: FontWeight.w600)),
            const SizedBox(height: 16),
            Row(
              children: [
                _badge(label),
                const SizedBox(width: 16),
                Text('${confidence.toStringAsFixed(1)}% CONFIDENCE', style: GoogleFonts.jetBrainsMono(color: TruthColors.cyanBright)),
              ],
            ),
            const SizedBox(height: 16),
            Text(verdict?['explanation'] as String? ?? '', style: GoogleFonts.inter(height: 1.5)),
            const SizedBox(height: 24),
            Text('SEC_04 // REASONING', style: GoogleFonts.jetBrainsMono(color: TruthColors.cyan)),
            ...reasoning.map((step) {
              final map = step as Map<String, dynamic>;
              return ListTile(
                dense: true,
                title: Text('${map['index']}. ${map['title']}', style: GoogleFonts.inter(fontWeight: FontWeight.w600)),
                subtitle: Text('${map['detail']}\nRefs: ${(map['evidence_ids'] as List?)?.join(', ')}', style: GoogleFonts.inter(color: TruthColors.muted)),
              );
            }),
            const SizedBox(height: 12),
            Text('SEC_05 // EVIDENCE', style: GoogleFonts.jetBrainsMono(color: TruthColors.cyan)),
            ...d.evidence.map((item) {
              final map = item as Map<String, dynamic>;
              return Card(
                color: TruthColors.panel,
                child: ListTile(
                  title: Text('${map['id']}  ${map['title']}', style: GoogleFonts.inter(fontWeight: FontWeight.w600)),
                  subtitle: Text('${map['text']}\n${map['url']} · ${map['store']} · ${map['stance']}', style: GoogleFonts.inter(color: TruthColors.muted, fontSize: 12)),
                ),
              );
            }),
            const SizedBox(height: 12),
            Text('SEC_06 // SOURCES', style: GoogleFonts.jetBrainsMono(color: TruthColors.cyan)),
            ...d.sources.map((item) {
              final map = item as Map<String, dynamic>;
              return Text('${map['tier']} ${map['score']}  ${map['url']}', style: GoogleFonts.jetBrainsMono(fontSize: 12, color: TruthColors.muted));
            }),
            const SizedBox(height: 16),
            Text('SEC_07 // ENTITY GRAPH', style: GoogleFonts.jetBrainsMono(color: TruthColors.cyan)),
            Wrap(
              spacing: 8,
              children: [
                for (final node in (d.graph?['nodes'] as List<dynamic>? ?? []))
                  Chip(label: Text('${node['type']}: ${node['label']}', style: GoogleFonts.jetBrainsMono(fontSize: 10)), backgroundColor: TruthColors.panelHigh),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _badge(String label) {
    final color = TruthColors.verdict(label);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(color: color.withOpacity(0.12), border: Border.all(color: color.withOpacity(0.4)), borderRadius: BorderRadius.circular(4)),
      child: Text('VERDICT: $label', style: GoogleFonts.jetBrainsMono(color: color, fontWeight: FontWeight.w700)),
    );
  }
}

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});
  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<HistoryRow> rows = [];

  @override
  void initState() {
    super.initState();
    api.history().then((value) => setState(() => rows = value));
  }

  @override
  Widget build(BuildContext context) {
    return Shell(
      active: 'history',
      child: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Text('SEC_08 // AUDIT HISTORY', style: GoogleFonts.jetBrainsMono(color: TruthColors.cyan)),
          const SizedBox(height: 16),
          if (rows.isEmpty) Text('No sealed dossiers yet.', style: GoogleFonts.inter(color: TruthColors.muted)),
          ...rows.map((row) {
            final v = row.json['verdict'] as String? ?? '—';
            return ListTile(
              onTap: () => context.go('/result/${row.json['id']}'),
              title: Text(row.json['original_input'] as String? ?? '', style: GoogleFonts.inter()),
              subtitle: Text('$v  ${((row.json['confidence'] as num?) ?? 0) * 100}%  ${row.json['agent_success']}', style: GoogleFonts.jetBrainsMono(fontSize: 11, color: TruthColors.verdict(v))),
            );
          }),
        ],
      ),
    );
  }
}

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});
  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  Analytics? data;

  @override
  void initState() {
    super.initState();
    api.analytics().then((value) => setState(() => data = value));
  }

  @override
  Widget build(BuildContext context) {
    final json = data?.json ?? {};
    final by = (json['by_verdict'] as Map<String, dynamic>?) ?? {};
    return Shell(
      active: 'analytics',
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('SEC_09 // EVALUATION', style: GoogleFonts.jetBrainsMono(color: TruthColors.cyan)),
            const SizedBox(height: 16),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                _kpi('TOTAL RUNS', '${json['total'] ?? 0}'),
                _kpi('AVG CONFIDENCE', ((json['avg_confidence'] as num?) ?? 0).toStringAsFixed(3)),
                _kpi('AGENT SUCCESS', ((json['agent_success_rate'] as num?) ?? 0).toStringAsFixed(3)),
                _kpi('SOURCE DIVERSITY', '${json['source_diversity'] ?? 0}'),
                _kpi('VERDICT CONSISTENCY', ((json['verdict_consistency'] as num?) ?? 0).toStringAsFixed(3)),
              ],
            ),
            const SizedBox(height: 24),
            ...by.entries.map((e) => Text('${e.key}: ${e.value}', style: GoogleFonts.jetBrainsMono(color: TruthColors.verdict(e.key)))),
          ],
        ),
      ),
    );
  }

  Widget _kpi(String label, String value) {
    return Container(
      width: 180,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: TruthColors.panel, border: Border.all(color: Colors.white.withOpacity(0.08))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: GoogleFonts.jetBrainsMono(fontSize: 10, color: TruthColors.muted)),
          const SizedBox(height: 8),
          Text(value, style: GoogleFonts.jetBrainsMono(fontSize: 22, color: TruthColors.cyanBright)),
        ],
      ),
    );
  }
}
