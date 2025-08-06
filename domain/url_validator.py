"""
URL validation service with comprehensive validation rules and custom exceptions.
"""

import re
import socket
import ssl
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, urljoin
import httpx
from datetime import datetime

from domain.exceptions import (
    URLValidationException,
    ValidationException,
    ServiceUnavailableException
)


class URLValidator:
    """Comprehensive URL validation service."""
    
    def __init__(self):
        self.blocked_domains = {
            'localhost', '127.0.0.1', '0.0.0.0', '::1',
            'example.com', 'test.com', 'invalid.com'
        }
        self.blocked_schemes = {'file', 'ftp', 'sftp', 'telnet', 'mailto'}
        self.max_url_length = 2048
        self.min_url_length = 10
        
    def validate_url(self, url: str, check_availability: bool = True) -> Dict[str, Any]:
        """
        Comprehensive URL validation.
        
        Args:
            url: The URL to validate
            check_availability: Whether to check if the URL is accessible
            
        Returns:
            Dict containing validation results
            
        Raises:
            URLValidationException: For various URL validation errors
        """
        try:
            # Basic format validation
            self._validate_url_format(url)
            
            # Parse URL components
            parsed_url = urlparse(url)
            
            # Validate scheme
            self._validate_scheme(parsed_url.scheme)
            
            # Validate domain
            self._validate_domain(parsed_url.netloc)
            
            # Validate URL length
            self._validate_url_length(url)
            
            # Check for blocked domains
            self._check_blocked_domains(parsed_url.netloc)
            
            # Validate URL structure
            self._validate_url_structure(parsed_url)
            
            # Optional availability check
            availability_info = {}
            if check_availability:
                availability_info = self._check_url_availability(url)
            
            return {
                "is_valid": True,
                "url": url,
                "parsed_url": {
                    "scheme": parsed_url.scheme,
                    "netloc": parsed_url.netloc,
                    "path": parsed_url.path,
                    "query": parsed_url.query,
                    "fragment": parsed_url.fragment
                },
                "availability": availability_info
            }
            
        except URLValidationException:
            raise
        except Exception as e:
            raise URLValidationException(
                message=f"Unexpected error during URL validation: {str(e)}",
                url=url,
                details={"error_type": type(e).__name__}
            )
    
    def _validate_url_format(self, url: str) -> None:
        """Validate basic URL format."""
        if not url:
            raise URLValidationException(
                message="URL cannot be empty",
                url=url
            )
        
        if not isinstance(url, str):
            raise URLValidationException(
                message="URL must be a string",
                url=str(url)
            )
        
        # Check for basic URL pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            raise URLValidationException(
                message="Invalid URL format",
                url=url,
                details={"expected_format": "http(s)://domain.com/path"}
            )
    
    def _validate_scheme(self, scheme: str) -> None:
        """Validate URL scheme."""
        if not scheme:
            raise URLValidationException(
                message="URL scheme is required",
                details={"scheme": scheme}
            )
        
        if scheme.lower() in self.blocked_schemes:
            raise URLValidationException(
                message=f"URL scheme '{scheme}' is not allowed",
                details={
                    "scheme": scheme,
                    "blocked_schemes": list(self.blocked_schemes)
                }
            )
        
        if scheme.lower() not in ['http', 'https']:
            raise URLValidationException(
                message=f"Only HTTP and HTTPS schemes are supported, got: {scheme}",
                details={"scheme": scheme}
            )
    
    def _validate_domain(self, netloc: str) -> None:
        """Validate domain name."""
        if not netloc:
            raise URLValidationException(
                message="Domain name is required",
                details={"netloc": netloc}
            )
        
        # Check for IP addresses
        if self._is_ip_address(netloc):
            if self._is_private_ip(netloc):
                raise URLValidationException(
                    message="Private IP addresses are not allowed",
                    details={"netloc": netloc}
                )
        else:
            # Validate domain name format
            domain_pattern = re.compile(
                r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
            )
            
            if not domain_pattern.match(netloc):
                raise URLValidationException(
                    message="Invalid domain name format",
                    details={"netloc": netloc}
                )
    
    def _validate_url_length(self, url: str) -> None:
        """Validate URL length."""
        if len(url) > self.max_url_length:
            raise URLValidationException(
                message=f"URL is too long. Maximum length is {self.max_url_length} characters",
                url=url,
                details={
                    "url_length": len(url),
                    "max_length": self.max_url_length
                }
            )
        
        if len(url) < self.min_url_length:
            raise URLValidationException(
                message=f"URL is too short. Minimum length is {self.min_url_length} characters",
                url=url,
                details={
                    "url_length": len(url),
                    "min_length": self.min_url_length
                }
            )
    
    def _check_blocked_domains(self, netloc: str) -> None:
        """Check if domain is in blocked list."""
        domain = netloc.lower().split(':')[0]  # Remove port if present
        
        if domain in self.blocked_domains:
            raise URLValidationException(
                message=f"Domain '{domain}' is not allowed",
                details={
                    "domain": domain,
                    "blocked_domains": list(self.blocked_domains)
                }
            )
    
    def _validate_url_structure(self, parsed_url) -> None:
        """Validate URL structure and components."""
        # Check for suspicious patterns
        suspicious_patterns = [
            r'javascript:', r'data:', r'vbscript:', r'file:',
            r'<script', r'<iframe', r'<object'
        ]
        
        url_string = parsed_url.geturl().lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, url_string):
                raise URLValidationException(
                    message=f"URL contains suspicious pattern: {pattern}",
                    details={"pattern": pattern}
                )
    
    def _check_url_availability(self, url: str) -> Dict[str, Any]:
        """Check if URL is accessible."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.head(url, follow_redirects=True)
                
                return {
                    "is_accessible": True,
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "content_length": response.headers.get("content-length"),
                    "server": response.headers.get("server", ""),
                    "last_modified": response.headers.get("last-modified", "")
                }
                
        except httpx.TimeoutException:
            raise URLValidationException(
                message="URL is not accessible (timeout)",
                url=url,
                details={"timeout": True}
            )
        except httpx.HTTPStatusError as e:
            return {
                "is_accessible": False,
                "status_code": e.response.status_code,
                "error": str(e)
            }
        except httpx.RequestError as e:
            raise URLValidationException(
                message=f"URL is not accessible: {str(e)}",
                url=url,
                details={"error": str(e)}
            )
    
    def _is_ip_address(self, netloc: str) -> bool:
        """Check if netloc is an IP address."""
        # Remove port if present
        host = netloc.split(':')[0]
        
        try:
            socket.inet_aton(host)
            return True
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, host)
                return True
            except socket.error:
                return False
    
    def _is_private_ip(self, netloc: str) -> bool:
        """Check if IP address is private."""
        host = netloc.split(':')[0]
        
        try:
            ip = socket.inet_aton(host)
            # Check for private IP ranges
            private_ranges = [
                (socket.inet_aton('10.0.0.0'), socket.inet_aton('10.255.255.255')),
                (socket.inet_aton('172.16.0.0'), socket.inet_aton('172.31.255.255')),
                (socket.inet_aton('192.168.0.0'), socket.inet_aton('192.168.255.255')),
                (socket.inet_aton('127.0.0.0'), socket.inet_aton('127.255.255.255'))
            ]
            
            for start, end in private_ranges:
                if start <= ip <= end:
                    return True
            return False
        except socket.error:
            return False
    
    def validate_custom_alias(self, alias: str) -> Dict[str, Any]:
        """Validate custom URL alias."""
        if not alias:
            raise ValidationException(
                message="Custom alias cannot be empty",
                field="custom_alias"
            )
        
        if len(alias) < 3:
            raise ValidationException(
                message="Custom alias must be at least 3 characters long",
                field="custom_alias",
                details={"min_length": 3, "current_length": len(alias)}
            )
        
        if len(alias) > 20:
            raise ValidationException(
                message="Custom alias must be at most 20 characters long",
                field="custom_alias",
                details={"max_length": 20, "current_length": len(alias)}
            )
        
        if not alias.isalnum():
            raise ValidationException(
                message="Custom alias must contain only alphanumeric characters",
                field="custom_alias",
                details={"alias": alias}
            )
        
        # Check for reserved words
        reserved_words = {
            'admin', 'api', 'auth', 'login', 'logout', 'register',
            'dashboard', 'settings', 'profile', 'help', 'about',
            'terms', 'privacy', 'contact', 'support'
        }
        
        if alias.lower() in reserved_words:
            raise ValidationException(
                message=f"Custom alias '{alias}' is reserved",
                field="custom_alias",
                details={
                    "alias": alias,
                    "reserved_words": list(reserved_words)
                }
            )
        
        return {
            "is_valid": True,
            "alias": alias,
            "length": len(alias)
        } 