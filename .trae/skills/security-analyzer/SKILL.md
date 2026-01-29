---
name: "security-analyzer"
description: "Automates security analysis of web applications by capturing traffic, filtering logs, and identifying vulnerabilities. Invoke when user wants to perform security assessment of a web application."
---

# Security Analyzer Skill

This skill automates the entire security analysis workflow for web applications, including:

1. **Browser Automation**: Launches browser with Burp Suite proxy to capture traffic
2. **Log Filtering**: Extracts JSON responses from Burp logs for analysis
3. **Security Assessment**: Analyzes traffic patterns and identifies potential vulnerabilities
4. **Report Generation**: Provides detailed analysis report with vulnerability recommendations

## When to Use This Skill

Invoke this skill when:
- You need to perform a security assessment of a web application
- You want to identify potential vulnerabilities in an application
- You need to analyze HTTP traffic for security issues
- You want to automate the process of capturing and analyzing web traffic

## How It Works

The security analyzer follows these steps:

1. **Launch Browser**: Opens Microsoft Edge with Burp Suite proxy configured
2. **Capture Traffic**: Navigates to the target URL and captures all HTTP traffic
3. **Filter Logs**: Extracts JSON responses from the Burp log file
4. **Analyze Traffic**: Identifies patterns and potential security vulnerabilities
5. **Generate Report**: Provides detailed analysis with vulnerability classifications and remediation recommendations

## Usage Example

```python
# Example: Analyze security of dipp.sf-express.com
from mcp.server.fastmcp import FastMCP
from MCPServer.Selenium import register_selenium_tool

# Create MCP server
mcp = FastMCP("SecurityAnalyzer")

# Register security tools
register_selenium_tool(mcp)

# Run server
mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)

# Then call the tool:
# selenium_automation(target_url="https://dipp.sf-express.com/")
```

## Available Tools

### 1. selenium_automation
```python
selenium_automation(target_url: str = "https://dipp.sf-express.com/", wait_time: int = 15) -> str
```
- **Description**: Launches browser, captures traffic, filters logs, and analyzes security
- **Parameters**:
  - `target_url`: Target URL to analyze (default: https://dipp.sf-express.com/)
  - `wait_time`: Manual operation wait time in seconds (default: 15)
- **Returns**: Analysis results and path to exported log file

### 2. filter_burp_log
```python
filter_burp_log(log_file: str = BURP_LOG_PATH) -> str
```
- **Description**: Filters existing Burp log file for JSON responses
- **Parameters**:
  - `log_file`: Path to Burp log file (default: from config.py)
- **Returns**: Filtering results and path to exported log file

## Analysis Output

The security analyzer generates:

1. **Filtered Log File**: Contains only JSON responses from the target application
2. **Security Analysis Report**: Includes:
   - Business process analysis
   - Identified vulnerabilities (with severity classification)
   - Detailed remediation recommendations
   - Risk assessment

## Configuration

### Required Files
- `MCPServer/Selenium.py`: Contains the security analysis tools
- `MCPServer/config.py`: Configuration file with paths
- Burp Suite: For traffic capture
- Microsoft Edge: For browser automation

### Configuration Parameters
- `BURP_LOG_PATH`: Path to Burp log file
- `TARGET_URL_KEYWORD`: Target URL keyword for filtering
- `TARGET_URL`: Default target URL
- `BURP_PROXY`: Burp Suite proxy configuration
- `EXPORT_DIR`: Directory for exported files

## Best Practices

1. **Pre-Analysis Preparation**:
   - Ensure Burp Suite is running with proxy enabled
   - Configure Burp to save logs to the specified path
   - Close unnecessary browser windows

2. **During Analysis**:
   - Interact with the application to trigger as many endpoints as possible
   - Test different user roles if applicable
   - Capture both authenticated and unauthenticated traffic

3. **Post-Analysis**:
   - Review the generated report carefully
   - Prioritize vulnerabilities based on severity
   - Implement recommended security controls

## Example Analysis Results

```
Operation completed!
Export file: C:\path\to\burp_json_valid_analysis.log
Filtered 20 JSON responses

Security Analysis Report:
=========================

Business Process Analysis:
- Frontend: dipp.sf-express.com
- API: dipp-api.sf-express.com
- Main endpoints: version check, token validation, announcement management

Identified Vulnerabilities:
1. HIGH: Unauthorized access to announcement data
2. MEDIUM: IDOR vulnerability in announcement IDs
3. LOW: Information disclosure in version endpoint

Remediation Recommendations:
1. Implement proper token validation for all API endpoints
2. Add access control checks for sensitive data
3. Remove sensitive information from public endpoints
```

## Troubleshooting

### Common Issues

1. **Browser Driver Not Found**
   - **Solution**: Ensure Microsoft Edge WebDriver is installed and in PATH

2. **Burp Log File Not Found**
   - **Solution**: Verify Burp is configured to save logs to the correct path

3. **Proxy Connection Issues**
   - **Solution**: Ensure Burp Suite is running and proxy settings are correct

4. **No JSON Responses Found**
   - **Solution**: Interact with the application more to trigger API requests

### Error Messages

- **"Error: Browser startup failed"**: Check Edge WebDriver installation
- **"Error: Burp log file not found"**: Verify Burp log path configuration
- **"No valid entries found"**: Application may not be using JSON responses

## Security Considerations

- **Ethical Use**: Only use this tool on applications you have permission to test
- **Privacy**: Respect user privacy and data protection regulations
- **Compliance**: Ensure testing activities comply with relevant laws and regulations
- **Authorization**: Obtain written authorization before performing security testing
This skill is intended for security professionals and developers to identify and fix security vulnerabilities in their own applications.
