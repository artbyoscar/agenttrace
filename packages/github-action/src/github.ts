import * as core from '@actions/core';
import * as github from '@actions/github';
import { GitHubContext, PRComment } from './types';

const COMMENT_MARKER = '<!-- agenttrace-evaluation-results -->';

export function getGitHubContext(): GitHubContext {
  const context = github.context;

  return {
    owner: context.repo.owner,
    repo: context.repo.repo,
    prNumber: context.payload.pull_request?.number,
    sha: context.sha,
    ref: context.ref,
    actor: context.actor,
  };
}

export async function postPRComment(
  token: string,
  context: GitHubContext,
  comment: PRComment
): Promise<void> {
  if (!context.prNumber) {
    core.warning('Not a pull request context, skipping PR comment');
    return;
  }

  const octokit = github.getOctokit(token);

  try {
    if (comment.isUpdate) {
      const existingComment = await findExistingComment(octokit, context);

      if (existingComment) {
        core.info(`Updating existing comment (ID: ${existingComment.id})`);
        await octokit.rest.issues.updateComment({
          owner: context.owner,
          repo: context.repo,
          comment_id: existingComment.id,
          body: `${COMMENT_MARKER}\n${comment.body}`,
        });
        return;
      }
    }

    core.info('Creating new PR comment');
    await octokit.rest.issues.createComment({
      owner: context.owner,
      repo: context.repo,
      issue_number: context.prNumber,
      body: `${COMMENT_MARKER}\n${comment.body}`,
    });
  } catch (error) {
    core.warning(`Failed to post PR comment: ${error}`);
  }
}

async function findExistingComment(
  octokit: ReturnType<typeof github.getOctokit>,
  context: GitHubContext
): Promise<{ id: number } | null> {
  if (!context.prNumber) {
    return null;
  }

  try {
    const { data: comments } = await octokit.rest.issues.listComments({
      owner: context.owner,
      repo: context.repo,
      issue_number: context.prNumber,
    });

    const existingComment = comments.find((comment) =>
      comment.body?.includes(COMMENT_MARKER)
    );

    return existingComment ? { id: existingComment.id } : null;
  } catch (error) {
    core.warning(`Failed to find existing comment: ${error}`);
    return null;
  }
}

export async function setCommitStatus(
  token: string,
  context: GitHubContext,
  state: 'success' | 'failure' | 'pending',
  description: string,
  targetUrl?: string
): Promise<void> {
  const octokit = github.getOctokit(token);

  try {
    await octokit.rest.repos.createCommitStatus({
      owner: context.owner,
      repo: context.repo,
      sha: context.sha,
      state,
      context: 'AgentTrace Evaluation',
      description,
      target_url: targetUrl,
    });
    core.info(`Commit status set to "${state}": ${description}`);
  } catch (error) {
    core.warning(`Failed to set commit status: ${error}`);
  }
}

export async function fetchBaselineResults(
  token: string,
  context: GitHubContext,
  baselineBranch: string,
  resultsPath: string
): Promise<any | null> {
  const octokit = github.getOctokit(token);

  try {
    core.info(`Fetching baseline results from ${baselineBranch}:${resultsPath}`);

    const { data } = await octokit.rest.repos.getContent({
      owner: context.owner,
      repo: context.repo,
      path: resultsPath,
      ref: baselineBranch,
    });

    if ('content' in data && data.content) {
      const content = Buffer.from(data.content, 'base64').toString('utf8');
      return JSON.parse(content);
    }

    return null;
  } catch (error: any) {
    if (error.status === 404) {
      core.info(`No baseline results found at ${baselineBranch}:${resultsPath}`);
      return null;
    }

    core.warning(`Failed to fetch baseline results: ${error}`);
    return null;
  }
}
