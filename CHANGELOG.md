# Changelog

All notable changes to ChronoSync will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned for v2.1.0 (Q3 2026)
- Student gap minimization algorithm
- Fixed instructor room assignment
- Multi-objective optimization framework
- Configurable optimization weights
- Enhanced quality metrics

See [FUTURE.md](FUTURE.md) for detailed roadmap.

---

## [2.0.1] - 2026-01-01

### Changed - Rebranding

**Major Rebranding: Schedule-AI → ChronoSync**

- **New Brand Identity**
  - New name: **ChronoSync** ("Harmonizing Academic Schedules")
  - New tagline: "Harmonizing Academic Schedules"
  - Modern visual identity with time/sync motifs
  - Updated all documentation and references

- **Package Updates**
  - Package name: `schedule-ai` → `chronosync`
  - CLI commands: `schedule-ai` → `chronosync`
  - CLI commands: `schedule-finetune` → `chronosync-finetune`
  - Repository URLs updated
  - Version bumped to 2.0.1

### Added

- **BRANDING.md**
  - Complete branding guidelines
  - Logo variations (large, medium, small, icon)
  - Color palette (Deep Blue #1E40AF, Electric Purple #7C3AED)
  - Typography guidelines (Montserrat, Inter, JetBrains Mono)
  - Badge designs for shields.io
  - Visual identity elements (clock/time motifs, network/sync motifs)
  - Usage guidelines (do's and don'ts)

- **FUTURE.md**
  - Detailed v2.1 roadmap
  - Feature 1: Student gap minimization algorithm with pseudocode
  - Feature 2: Fixed instructor room assignment with implementation plan
  - Feature 3: Multi-objective optimization framework
  - Algorithm comparison (v2.0 vs v2.1)
  - Expected improvements and success criteria
  - Implementation timeline (Q1-Q3 2026)

- **CHANGELOG.md**
  - This file
  - Version history tracking
  - Structured changelog format

- **New Badges**
  - ChronoSync version badge (purple #7C3AED)
  - Updated Python badge (blue #1E40AF)
  - Updated Status badge (green #10B981)
  - Updated License badge (orange #F59E0B)

### Documentation

- **README.md Updates**
  - Header: "Schedule-AI" → "ChronoSync"
  - Subtitle: Updated to "Harmonizing Academic Schedules with Intelligence"
  - All brand references updated throughout
  - Added 6th competitive advantage: "Future-Ready Optimization"
  - Added optimization row in comparison table
  - Updated git clone commands
  - Updated footer with new branding

- **setup.py Updates**
  - Package name: `chronosync`
  - Version: `2.0.1`
  - Description updated with new tagline
  - Entry points updated with new CLI command names
  - URLs updated to chronosync repository
  - Keywords updated to include "chronosync" and "optimization"

- **Updated URLs**
  - Repository: `schedule-ai` → `chronosync`
  - Documentation links updated
  - Issue tracker links updated
  - Star history badge updated

### Technical Details

**No Breaking Changes**
- Core algorithm unchanged
- All existing features preserved
- Input/output formats remain compatible
- Configuration files compatible

**Compatibility**
- Python 3.8+ (unchanged)
- All dependencies unchanged
- Existing schedules fully compatible
- Backward compatible with v2.0.0

---

## [2.0.0] - 2025-12-XX

### Changed - Major Restructuring

**Project Reorganization**

- **Directory Structure**
  - Created professional project layout
  - `src/` - All source code
  - `data/` - Input and output data (separated)
  - `config/` - Configuration files
  - `docs/` - Documentation
  - `tests/` - Test files (structure created)

- **Data Organization**
  - Separated input data (data awal) → `data/input/program_studies/`
  - Separated output data (hasil) → `data/output/`
  - Per-program subdirectories for better organization
  - Clear distinction between source data and generated results

- **Code Modularization**
  - `src/core/` - Core scheduling engine
  - `src/analysis/` - Analysis and verification tools
  - `src/scripts/` - Utility and rescue scripts
  - Better separation of concerns

### Added

- **Documentation**
  - Comprehensive README.md (1,267 lines)
  - Problem statement with NP-Complete explanation
  - 5 ASCII architecture diagrams
  - Algorithm pseudocode with complexity analysis
  - Competitive comparison table (10 aspects)
  - Phase-by-phase execution workflow
  - 40+ code examples
  - 5 unique selling points

- **Configuration System**
  - `config/settings.py` - Core settings and parameters
  - `config/constraints.yaml` - Constraint definitions
  - `requirements.txt` - Dependency management
  - `.gitignore` - Git ignore rules
  - `setup.py` - Package installation configuration

- **Data Documentation**
  - `data/input/README.md` - Input data format guide
  - `data/output/README.md` - Output interpretation guide
  - Per-program directory structure
  - File format specifications

- **Algorithm Documentation**
  - `docs/README_ALGORITHM.md` - Algorithm details
  - Greedy scheduling algorithm explanation
  - Conflict resolution process
  - When to use this system
  - Complexity analysis

### Features

**Core Capabilities** (Existing, Now Documented)
- Multi-program scheduling (6 programs)
- Constraint satisfaction (15+ constraint types)
- Auto conflict resolution (iterative, max 120 iterations)
- Priority-based scheduling (PWK fixed at priority 100)
- Hybrid mode support (Zoom + in-person)
- Fine-tuning without rebuild
- 14 analysis & verification tools

**Supported Programs**
- Informatika
- Pengairan (Irrigation)
- Teknik Elektro
- PWK (Urban Planning) - Fixed schedule
- Arsitektur
- MKDU (General Education)

### Technical Achievements

- ✅ 500+ courses scheduled automatically
- ✅ 0 instructor conflicts
- ✅ 0 room conflicts
- ✅ 0 student conflicts
- ✅ PWK schedule 100% preserved
- ✅ Execution time: 2-5 minutes
- ✅ Fine-tuning capability

### Version Control

- Used `git mv` for all file relocations (46 files moved)
- Preserved Git history for all files
- Clean commit structure

---

## [1.0.0] - 2025-XX-XX

### Added - Initial Release

**Core Features**
- Basic greedy scheduling algorithm
- Multi-program scheduling support
- PWK priority preservation
- Conflict detection and resolution
- Excel input/output support

**Scheduling Capabilities**
- Instructor conflict prevention
- Room conflict prevention
- Student schedule conflict prevention
- Semester-based rules (Semester 1 = Zoom)
- Class type rules (Regular = Weekdays, Non-Regular = Weekend)
- MKDU Saturday-only scheduling

**Output Generation**
- Multiple Excel sheets per program
- Master schedule combining all programs
- Formatted output with institutional headers

**Limitations**
- Monolithic code structure
- Limited documentation
- Mixed input/output data
- No formal configuration system
- No optimization for student gaps
- No optimization for instructor room assignment

---

## Version History Summary

| Version | Date | Type | Description |
|---------|------|------|-------------|
| **2.0.1** | 2026-01-01 | Rebranding | ChronoSync rebranding + future roadmap |
| **2.0.0** | 2025-12-XX | Major | Project restructuring + comprehensive docs |
| **1.0.0** | 2025-XX-XX | Initial | First working version |

---

## Migration Guide

### From v2.0.0 to v2.0.1

**No Code Changes Required**

This is a rebranding release with no breaking changes to functionality.

**Optional Updates:**

1. **Update CLI Commands** (if using installed package):
   ```bash
   # Old command
   schedule-ai

   # New command
   chronosync
   ```

   ```bash
   # Old fine-tune command
   schedule-finetune

   # New fine-tune command
   chronosync-finetune
   ```

2. **Update Package Name** (if installed via pip):
   ```bash
   # Uninstall old
   pip uninstall schedule-ai

   # Install new
   pip install -e .
   ```

3. **Update Documentation References**:
   - Change "Schedule-AI" → "ChronoSync" in your documentation
   - Update repository URLs if you forked

**Unchanged:**
- All Python imports remain the same (`from core.jadwal import ...`)
- All data formats compatible
- All configuration files compatible
- All existing schedules work without modification

---

## Future Roadmap

### v2.1.0 (Q3 2026) - Optimization Release

**Major Features:**
- Student gap minimization
- Fixed instructor room assignment
- Multi-objective optimization
- Configurable optimization weights

**Expected Improvements:**
- 60% reduction in student gaps
- 70% instructors with fixed rooms
- Compactness score: 85+
- Enhanced quality metrics

See [FUTURE.md](FUTURE.md) for complete details.

### v2.2.0 (Future) - Advanced Features

**Planned:**
- Machine learning for weight tuning
- Genetic algorithm optimization
- Visual schedule editor (drag & drop)
- Cloud-based optimization service
- Mobile app for schedule viewing
- Email notifications for changes

### v3.0.0 (Future) - Enterprise Release

**Planned:**
- Multi-tenant support
- API for integration
- Real-time collaborative editing
- Advanced analytics dashboard
- Automated schedule approval workflow
- Integration with university SIS systems

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) (to be created) for guidelines.

**Priority Areas:**
- v2.1 optimization features
- Test coverage improvements
- Documentation enhancements
- Performance optimizations
- Bug fixes

---

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/chronosync/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/chronosync/discussions)
- **Documentation:** [README.md](README.md)

---

<div align="center">

**ChronoSync Changelog**

Built with ❤️ for Indonesian Universities

[View on GitHub](https://github.com/yourusername/chronosync) | [Documentation](README.md) | [Roadmap](FUTURE.md)

</div>
