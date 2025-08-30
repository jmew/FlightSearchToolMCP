import type { Request, Response } from 'express';
import { FileSearchFactory } from '@google/gemini-cli-core';

export async function suggestionHandler(req: Request, res: Response) {
  const query = req.query['query'] as string;
  if (!query) {
    return res.json({ suggestions: [] });
  }

  try {
    if (query.startsWith('/')) {
      const slashCommands: Record<
        string,
        { description: string; subCommands?: string[] }
      > = {
        help: { description: 'Show help' },
        chat: {
          description: 'Manage conversation history',
          subCommands: ['save', 'resume', 'list', 'delete'],
        },
        clear: { description: 'Clear the screen' },
        theme: { description: 'Change the theme' },
        mcp: { description: 'List MCP servers' },
        memory: {
          description: 'Manage memory',
          subCommands: ['show', 'add', 'refresh'],
        },
        stats: { description: 'Show session stats' },
      };

      const parts = query.substring(1).split(' ');
      const command = parts[0];
      const partial = parts.length > 1 ? parts[1] : '';

      if (parts.length === 1) {
        const suggestions = Object.keys(slashCommands)
          .filter((c) => c.startsWith(command))
          .map((c) => `/${c}`);
        return res.json({ suggestions });
      } else if (parts.length > 1 && slashCommands[command]?.subCommands) {
        const suggestions =
          slashCommands[command]?.subCommands
            ?.filter((sc) => sc.startsWith(partial))
            .map((sc) => `/${command} ${sc}`) || [];
        return res.json({ suggestions });
      }
      return res.json({ suggestions: [] });
    } else if (query.startsWith('@')) {
      const searchPattern = query.substring(1);
      const fileSearch = FileSearchFactory.create({
        projectRoot: process.cwd(),
        ignoreDirs: [],
        useGitignore: true,
        useGeminiignore: true,
        cache: true,
        cacheTtl: 30,
        enableRecursiveFileSearch: true,
        disableFuzzySearch: false,
      });
      await fileSearch.initialize();
      const results = await fileSearch.search(searchPattern, {
        maxResults: 10,
      });
      const suggestions = results.map((r: string) => `@${r}`);
      return res.json({ suggestions });
    } else {
      return res.json({ suggestions: [] });
    }
  } catch (error) {
    console.error('Error fetching suggestions:', error);
    return res.status(500).json({ error: 'Failed to fetch suggestions.' });
  }
}
