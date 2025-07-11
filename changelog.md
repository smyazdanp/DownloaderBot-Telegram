# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2024-01-20

### Added
- Complete rewrite with aiogram 3.x
- Advanced download manager with resume support
- Real-time progress tracking with speed and ETA
- Admin panel with comprehensive statistics
- User management system (VIP, ban, limits)
- File splitting for files larger than 2GB
- SQLite database with transaction support
- Docker support with docker-compose
- GitHub Actions CI/CD pipeline
- Automatic cleanup of old files
- Multi-language support (Persian/English)
- Charts and visualizations for statistics
- Broadcast messaging for admins
- File upload with unique codes
- Rate limiting protection
- Detailed logging system

### Changed
- Migrated from aiogram 2.x to 3.x
- Improved error handling and retry logic
- Enhanced security with input validation
- Better file type detection
- Optimized database queries
- Updated UI with inline keyboards

### Fixed
- File sending issues
- Settings not saving properly
- Memory leaks in large file handling
- Timeout issues for slow downloads

### Security
- Added input sanitization
- Implemented rate limiting
- Secure file handling
- Admin-only command protection

## [2.0.0] - 2023-12-01

### Added
- Basic admin panel
- User statistics
- Daily download limits
- VIP system

### Changed
- Improved download speed
- Better error messages

### Fixed
- Connection timeout issues
- Database corruption on crash

## [1.0.0] - 2023-10-15

### Added
- Initial release
- Basic file download functionality
- Simple user management
- SQLite database

[3.0.0]: https://github.com/yourusername/telegram-downloader-bot/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/yourusername/telegram-downloader-bot/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/yourusername/telegram-downloader-bot/releases/tag/v1.0.0