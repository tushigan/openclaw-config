// 总控BOSS skill - 由 SKILL.md frontmatter 驱动
module.exports = {
  handler: async ({ input, context }) => {
    return {
      type: 'workflow',
      instructions: 'Follow the workflow defined in SKILL.md'
    };
  }
};
