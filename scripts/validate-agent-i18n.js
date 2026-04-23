#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");
const agentDir = path.join(repoRoot, "agent");
const localesDir = path.join(agentDir, "locales");

const personaFiles = ["SOUL.md", "IDENTITY.md", "USER.md", "TOOLS.md", "AGENTS.md"];
const supportedLocales = ["zh-CN", "zh-TW"];
const strictMode = process.argv.includes("--strict");
const jsonMode = process.argv.includes("--json");

function existsAndNonEmpty(filePath) {
  try {
    const stat = fs.statSync(filePath);
    return stat.isFile() && stat.size > 0;
  } catch {
    return false;
  }
}

function extractH2Headings(filePath) {
  const content = fs.readFileSync(filePath, "utf8");
  return content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.startsWith("## "))
    .map((line) => line.replace(/^##\s+/, ""));
}

function parseH2Sections(filePath) {
  const content = fs.readFileSync(filePath, "utf8");
  const lines = content.split(/\r?\n/);
  const sections = [];
  let current = null;

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (line.startsWith("## ")) {
      if (current) {
        sections.push(current);
      }
      current = {
        heading: line.replace(/^##\s+/, ""),
        contentLines: [],
      };
      continue;
    }

    if (current) {
      current.contentLines.push(rawLine);
    }
  }

  if (current) {
    sections.push(current);
  }

  return sections;
}

function countMeaningfulLines(lines) {
  return lines
    .map((line) => line.trim())
    .filter((line) => {
      if (!line) return false;
      if (line === "---") return false;
      if (line.startsWith("#")) return false;
      return true;
    }).length;
}

const errors = [];

function outputAndExit() {
  if (jsonMode) {
    const payload = {
      ok: errors.length === 0,
      mode: strictMode ? "strict" : "default",
      checks: {
        baseFiles: personaFiles,
        locales: supportedLocales,
      },
      errorCount: errors.length,
      errors,
    };
    const output = JSON.stringify(payload, null, 2);
    if (errors.length > 0) {
      console.error(output);
      process.exit(1);
    }
    console.log(output);
    process.exit(0);
  }

  if (errors.length > 0) {
    console.error("Persona i18n validation failed:");
    for (const error of errors) {
      console.error(`- ${error}`);
    }
    process.exit(1);
  }

  console.log(`Persona i18n validation passed${strictMode ? " (strict mode)" : ""}.`);
  process.exit(0);
}

for (const file of personaFiles) {
  const basePath = path.join(agentDir, file);
  if (!existsAndNonEmpty(basePath)) {
    errors.push(`Missing or empty base persona file: agent/${file}`);
  }
}

for (const locale of supportedLocales) {
  for (const file of personaFiles) {
    const overlayPath = path.join(localesDir, locale, file);
    if (!existsAndNonEmpty(overlayPath)) {
      errors.push(`Missing or empty locale overlay: agent/locales/${locale}/${file}`);
      continue;
    }

    if (strictMode) {
      const basePath = path.join(agentDir, file);
      if (!existsAndNonEmpty(basePath)) {
        continue;
      }

      const baseH2 = extractH2Headings(basePath);
      const localeH2 = extractH2Headings(overlayPath);

      if (localeH2.length < baseH2.length) {
        errors.push(
          `Strict mode: agent/locales/${locale}/${file} has ${localeH2.length} H2 sections, expected at least ${baseH2.length}`
        );
      }

      if (localeH2.length !== baseH2.length) {
        errors.push(
          `Strict mode: agent/locales/${locale}/${file} must keep the same H2 section count/order slots as base (${baseH2.length}), got ${localeH2.length}`
        );
      }

      const baseSections = parseH2Sections(basePath);
      const localeSections = parseH2Sections(overlayPath);
      const comparableCount = Math.min(baseSections.length, localeSections.length);

      for (let i = 0; i < comparableCount; i += 1) {
        const baseSection = baseSections[i];
        const localeSection = localeSections[i];

        const baseMinContent = Math.max(1, Math.ceil(countMeaningfulLines(baseSection.contentLines) * 0.2));
        const localeContentCount = countMeaningfulLines(localeSection.contentLines);

        if (localeContentCount < baseMinContent) {
          errors.push(
            `Strict mode: agent/locales/${locale}/${file} section ${i + 1} ("${localeSection.heading}") is too short (${localeContentCount} lines), expected at least ${baseMinContent}`
          );
        }

        if (localeSection.heading.length === 0) {
          errors.push(`Strict mode: agent/locales/${locale}/${file} has an empty H2 heading at section ${i + 1}`);
        }

        if (localeContentCount === 0) {
          errors.push(
            `Strict mode: agent/locales/${locale}/${file} section ${i + 1} ("${localeSection.heading}") has no meaningful content`
          );
        }
      }
    }
  }
}

outputAndExit();
