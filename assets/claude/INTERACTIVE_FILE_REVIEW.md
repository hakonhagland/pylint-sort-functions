# Interactive File Review Methodology

This document describes the systematic approach for conducting interactive code reviews with Claude Code. This methodology ensures thorough analysis while preventing premature changes and building comprehensive understanding.

## Overview

Interactive file review is a structured process where the user guides the analysis through questions and answers, building up knowledge before making any modifications. This approach leads to more informed decisions and better outcomes.

## The Four-Phase Process

### Phase 1: Question & Answer 🤔

This phase is split into two sub-phases for better organization:

#### Phase 1a: User-Led Questions 👤
- **User drives the initial exploration** by asking specific questions about the code
- **Claude provides detailed answers** explaining implementation choices, alternatives, and implications
- **Focus on areas of user interest** and specific concerns

#### Phase 1b: Claude-Led Questions 🤖
- **Claude asks targeted questions** to fill knowledge gaps and explore areas not covered by user
- **Comprehensive coverage** of all aspects: functionality, maintainability, performance, edge cases
- **User provides insights** about intended behavior, constraints, and priorities

**Combined Phase 1 Outcome:** Complete understanding of the file from both perspectives before any modifications

### Phase 2: Analysis & Knowledge Building 📚
- **Comprehensive understanding** is built through systematic Q&A
- **Multiple perspectives** are explored (functionality, maintainability, performance, etc.)
- **Edge cases and alternatives** are discussed
- **Context and rationale** behind design decisions are clarified

### Phase 3: Planning & Strategy 📋
- **Review insights** are synthesized into improvement opportunities
- **Priorities are established** based on impact and effort
- **Implementation approach** is planned with user input
- **Dependencies and impacts** on other files are considered

### Phase 4: Implementation & Verification ✅
- **Informed changes** are made based on complete understanding
- **Quality standards** are maintained throughout
- **Testing and verification** ensure no regressions
- **Documentation updates** reflect the improvements

## Benefits of This Approach

### For Users
- **Full control** over the review process and priorities
- **Deep understanding** of the codebase before changes
- **Informed decision-making** based on complete context
- **Learning opportunity** through detailed explanations

### For Code Quality
- **Prevents premature optimization** and hasty changes
- **Ensures comprehensive analysis** of all aspects
- **Maintains consistency** with project standards
- **Reduces risk** of introducing bugs or regressions

### For Project Management
- **Clear documentation** of decisions and rationale
- **Reusable methodology** for future reviews
- **Knowledge sharing** with team members
- **Audit trail** of improvements and reasoning

## Best Practices

### Question Types
- **Functionality**: "What does this function do and why is it implemented this way?"
- **Architecture**: "How does this component fit into the overall system?"
- **Alternatives**: "What other approaches could we use here?"
- **Edge Cases**: "What happens when inputs are invalid or unexpected?"
- **Performance**: "Are there any performance implications of this approach?"
- **Maintainability**: "How easy is this code to understand and modify?"

### Review Focus Areas
- **Code Organization**: Structure, separation of concerns, modularity
- **Documentation**: Comments, docstrings, inline explanations
- **Error Handling**: Exception handling, validation, edge cases
- **Testing**: Test coverage, test quality, missing scenarios
- **Performance**: Efficiency, scalability, resource usage
- **User Experience**: CLI design, output formatting, error messages

### Quality Gates
- **Understanding First**: Don't modify until you understand completely
- **Test Coverage**: Maintain or improve test coverage with changes
- **Code Standards**: Follow project conventions and style guides
- **Documentation**: Update relevant documentation with changes
- **Verification**: Test changes thoroughly before completion

## Example Usage

### Starting an Interactive Review

```markdown
## Interactive Review of [filename]

### Phase 1: Questions & Answers
**Q1**: [User question about specific code section]
**A1**: [Claude's detailed explanation]

**Q2**: [Follow-up question about alternatives]
**A2**: [Analysis of different approaches]

### Phase 2: Insights Summary
- Key findings from the Q&A session
- Areas for improvement identified
- Priorities and impact assessment

### Phase 3: Implementation Plan
- Specific changes to be made
- Order of implementation
- Testing strategy

### Phase 4: Execution
- Make the planned changes
- Verify functionality
- Update documentation
```

## Integration with Development Workflow

### Pre-Review Checklist
- [ ] File is ready for review (no pending changes)
- [ ] Test suite is passing
- [ ] Context is understood (purpose, dependencies, etc.)

### During Review
- [ ] Focus on understanding before changing
- [ ] Ask specific, targeted questions
- [ ] Explore multiple perspectives
- [ ] Document insights and decisions

### Post-Review
- [ ] Verify all changes work correctly
- [ ] Update tests if needed
- [ ] Update documentation
- [ ] Commit with clear, descriptive messages

## Tips for Effective Reviews

### For Users
1. **Start with high-level questions** then drill down into specifics
2. **Ask about alternatives** to understand trade-offs
3. **Challenge assumptions** to ensure they're still valid
4. **Consider edge cases** and error conditions
5. **Think about future maintainability** and extensibility

### For Implementation
1. **Make small, focused changes** rather than large rewrites
2. **Test incrementally** as you make changes
3. **Maintain backward compatibility** unless intentionally breaking
4. **Document the reasoning** behind significant changes
5. **Consider performance implications** of modifications

## Success Metrics

A successful interactive review should result in:
- **Improved code quality** with measurable metrics
- **Enhanced understanding** of the codebase
- **Better documentation** and maintainability
- **Maintained or improved test coverage**
- **Clear rationale** for all changes made

## Conclusion

Interactive file review transforms code review from a reactive process into a proactive, educational experience. By building understanding first and implementing changes second, we create better code, better documentation, and better developers.

This methodology can be applied to any codebase, any file type, and any complexity level. The key is maintaining the discipline of understanding before acting.

---

*This methodology was developed during the pylint-sort-functions project interactive reviews and has proven effective for thorough, high-quality code improvements.*
