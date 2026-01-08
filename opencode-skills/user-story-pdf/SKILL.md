---
name: user-story-pdf
description: Generate professional PDF documents from user story checkpoints. Creates shareable, print-ready documentation for product teams. Use when asked to "create PDF from checkpoint", "export user stories", "generate PDF", or "share stories with team".
compatibility: Requires Google Chrome or Chromium for PDF generation
metadata:
  author: opencode
  version: "1.0"
---

# User Story PDF Generation

Use this skill when the user asks to:
- "Create PDF from checkpoint" or "export user stories to PDF"
- "Generate a PDF for my product team"
- "Create shareable documentation from user stories"
- "Export checkpoint-XX to PDF"

## Quick Start

1. Read the checkpoint file to identify stories
2. Gather all referenced story files
3. Create HTML document with professional styling
4. Run the generation script: `scripts/generate-pdf.sh`

## Prerequisites

Before generating a PDF, ensure:
1. A checkpoint file exists: `agent-plans/user-stories/checkpoint-{NN}.md`
2. Individual user story files exist in domain folders
3. Google Chrome is installed

## Step-by-Step Process

### Step 1: Read the Checkpoint

Read `agent-plans/user-stories/checkpoint-{NN}.md` to understand:
- Which stories to include (from "Stories in This Checkpoint" table)
- Story statuses (Active, Superseded, Deferred, Fixed)
- Domain structure and evolution
- Key decisions and summary

### Step 2: Gather All Story Files

For each story in the checkpoint, read the corresponding files:
- Overview files: `{NN}-{domain}/{NN}-00-overview.md`
- Individual stories: `{NN}-{domain}/{NN}-{NN}-{story-name}.md`

Extract from each story:
- Story ID and title
- Status
- Story narrative (As a... I want... so that...)
- Acceptance criteria (Given/When/Then format)
- Edge cases table
- Form fields (simplified - type and required only)

### Step 3: Create HTML Document

Create `agent-plans/user-stories/user-stories-document.html` with:

**Required sections:**
1. Cover page (project name, checkpoint, date, story counts)
2. Table of contents
3. Executive summary with statistics
4. Checkpoint overview with domain breakdown
5. Detailed stories organized by domain
6. Implementation roadmap (if applicable)
7. Appendices (personas, flows, references)

**Use styling from:** `assets/template.css`

### Step 4: Generate PDF

Run the generation script:

```bash
# From the user-stories directory
./scripts/generate-pdf.sh

# Or with options
./scripts/generate-pdf.sh -d agent-plans/user-stories -o ProjectName-Checkpoint-01.pdf
```

Script options:
- `-i, --input FILE` - Input HTML file (default: user-stories-document.html)
- `-o, --output FILE` - Output PDF filename
- `-d, --directory DIR` - Working directory
- `-h, --help` - Show help

### Step 5: Report Results

After generation, report to user:
- File path
- File size
- Page count
- Story count summary

## HTML Structure

### Cover Page

```html
<div class="cover-page">
    <div class="cover-title">{Project Name}</div>
    <div class="cover-subtitle">User Stories & Product Requirements</div>
    <div class="cover-meta">
        <div class="cover-meta-item">
            <span class="cover-meta-label">Checkpoint:</span> {NN}
        </div>
        <div class="cover-meta-item">
            <span class="cover-meta-label">Date:</span> {YYYY-MM-DD}
        </div>
        <div class="cover-meta-item">
            <span class="cover-meta-label">Total Stories:</span> {count}
        </div>
        <div class="cover-meta-item">
            <span class="cover-meta-label">Status:</span> {X Active, Y Superseded, Z Deferred}
        </div>
    </div>
</div>
```

### Story Card

```html
<div class="story-card">
    <div class="story-header">
        <span class="story-id">US-{NN}-{NN}</span>
        <span class="story-status status-active">Active</span>
    </div>
    <div class="story-title">{Story Title}</div>
    <div class="story-narrative">
        As a <strong>{persona}</strong>, I want to <strong>{action}</strong> 
        so that <strong>{benefit}</strong>.
    </div>
    
    <div class="criteria-section">
        <h4>Acceptance Criteria</h4>
        <div class="criterion">
            <div class="criterion-title">{Scenario Name}</div>
            <div class="criterion-description">
                <strong>Given</strong> {precondition}<br/>
                <strong>When</strong> {action}<br/>
                <strong>Then</strong> {result}
            </div>
        </div>
    </div>
    
    <h4>Edge Cases</h4>
    <table>
        <thead><tr><th>Scenario</th><th>Behavior</th></tr></thead>
        <tbody>
            <tr><td>{scenario}</td><td>{behavior}</td></tr>
        </tbody>
    </table>
</div>
```

### Status Badge Classes

| Status | CSS Class |
|--------|-----------|
| Active | `status-active` (green) |
| Superseded | `status-superseded` (red) |
| Deferred | `status-deferred` (yellow) |
| Fixed | `status-fixed` (blue) |

## Content Guidelines

### Include in PDF

| Section | Include | Format |
|---------|---------|--------|
| Story ID | Yes | e.g., US-00-01 |
| Status badge | Yes | Color-coded |
| Story narrative | Yes | As a... I want... so that... |
| Acceptance criteria | Yes | Gherkin (Given/When/Then) |
| Edge cases | Yes | Table |
| Form fields | If applicable | Type and required only |
| Flow diagrams | If important | ASCII preserved |

### Exclude from PDF (keep in agent-plans)

- API endpoints with schemas
- Detailed validation rules
- Code examples
- Directory structures
- Implementation steps

## Files in This Skill

| Path | Purpose |
|------|---------|
| `SKILL.md` | This file - instructions |
| `scripts/generate-pdf.sh` | PDF generation script |
| `assets/template.css` | Professional CSS styling |

## Cross-Platform Chrome Paths

The script auto-detects Chrome on:

| Platform | Locations Checked |
|----------|-------------------|
| macOS | `/Applications/Google Chrome.app/...` |
| Linux | `google-chrome`, `chromium-browser`, `chromium` |
| Windows (WSL) | `/mnt/c/Program Files/Google/Chrome/...` |

## Example Output

```
╔══════════════════════════════════════════════════════╗
║          User Story PDF Generator                    ║
╚══════════════════════════════════════════════════════╝

ℹ Working directory: /project/agent-plans/user-stories
✓ Found input file: user-stories-document.html
ℹ Output file: User-Stories-Checkpoint-01.pdf
✓ Found Chrome: /Applications/Google Chrome.app/...
ℹ Generating PDF...

╔══════════════════════════════════════════════════════╗
║                   PDF Generated!                     ║
╚══════════════════════════════════════════════════════╝

✓ File: /project/agent-plans/user-stories/User-Stories-Checkpoint-01.pdf
✓ Size: 1.2M
✓ Pages: 8
```

## Checklist

- [ ] Read checkpoint file to identify all stories
- [ ] Read each referenced story file
- [ ] Note story statuses (Active, Superseded, Deferred, Fixed)
- [ ] Create HTML with cover page, TOC, executive summary
- [ ] Add stories organized by domain
- [ ] Include acceptance criteria in Gherkin format
- [ ] Add edge cases tables
- [ ] Apply professional styling from `assets/template.css`
- [ ] Run `scripts/generate-pdf.sh`
- [ ] Verify PDF created successfully
- [ ] Report file location and size to user

## Relationship to Other Skills

| Skill | Relationship |
|-------|--------------|
| `user-stories` | Source content for PDF |
| `agent-plan` | Technical details NOT included in PDF |
| `agent-context` | Not related |
