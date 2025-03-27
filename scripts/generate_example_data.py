#!/usr/bin/env python3
"""
Generate example chat data for demonstrating the Cursor chat extraction.
This script creates realistic-looking chat conversations in the same format
as the extraction scripts would produce.
"""

import argparse
import random
import datetime
import os
from typing import List, Dict, Tuple, Optional

# Sample programming languages and topics for realistic examples
LANGUAGES = ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust", "Ruby"]
TOPICS = ["API", "database", "frontend", "algorithm", "UI", "CLI", "testing", "deployment"]
CONCEPTS = ["class", "function", "module", "component", "service", "utility", "pattern"]
FRAMEWORKS = {
    "Python": ["Django", "Flask", "FastAPI", "Pandas", "TensorFlow", "PyTorch"],
    "JavaScript": ["React", "Angular", "Vue", "Express", "Node.js", "Next.js"],
    "TypeScript": ["React", "Angular", "Vue", "Nest.js", "Express", "Next.js"],
    "Java": ["Spring Boot", "Hibernate", "Jakarta EE", "Android SDK"],
    "C++": ["Qt", "Boost", "STL", "OpenGL"],
    "Go": ["Gin", "Echo", "Fiber", "GoLand"],
    "Rust": ["Actix", "Rocket", "Tokio", "wasm-bindgen"],
    "Ruby": ["Rails", "Sinatra", "Roda"]
}

# Sample function and variable names
FUNCTION_NAMES = ["get_data", "process_item", "create_user", "handle_request", 
                  "parse_input", "validate_form", "update_state", "fetch_results"]
VARIABLE_NAMES = ["data", "result", "user", "item", "config", "options", 
                 "response", "client", "service", "manager", "handler"]

def generate_timestamp() -> str:
    """Generate a random timestamp within the last month."""
    now = datetime.datetime.now()
    days_ago = random.randint(0, 30)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    
    timestamp = now - datetime.timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def generate_lorem_ipsum(sentences: int = 3) -> str:
    """Generate lorem ipsum text with the specified number of sentences."""
    lorem_chunks = [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "Nullam euismod, nisi vel consectetur interdum, nisl nisi aliquam eros, vel auctor nisl nisl vel lectus.",
        "Donec eget ex magna. Interdum et malesuada fames ac ante ipsum primis in faucibus.",
        "Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae.",
        "Aliquam finibus fermentum purus, ac vulputate augue fringilla id.",
        "Cras porta malesuada eros. Sed sit amet turpis gravida, ullamcorper dui quis, facilisis libero.",
        "Duis varius tellus eget massa tempus dignissim. Integer id imperdiet felis.",
        "Pellentesque fringilla ipsum nec justo tempus, et fringilla nisl finibus.",
        "Ut vel est felis. Cras eget vestibulum lorem, et efficitur dolor.",
        "Donec placerat ultrices nibh, a hendrerit mi fermentum sit amet."
    ]
    
    selected = random.sample(lorem_chunks, min(sentences, len(lorem_chunks)))
    return " ".join(selected)

def generate_code_example(language: str, complexity: str = "medium") -> str:
    """Generate a code example in the specified language with the given complexity."""
    language_code_examples = {
        "Python": {
            "simple": """def add_numbers(a, b):
    \"\"\"Add two numbers and return the result.\"\"\"
    return a + b

# Example usage
result = add_numbers(5, 10)
print(f"The result is: {result}")""",
            "medium": """import json
from typing import Dict, List, Optional

class DataProcessor:
    \"\"\"Process data from various sources.\"\"\"
    
    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.data = []
    
    def load_from_file(self, filename: str) -> bool:
        \"\"\"Load data from a JSON file.\"\"\"
        try:
            with open(filename, 'r') as f:
                self.data = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def process(self) -> List[Dict]:
        \"\"\"Process the loaded data.\"\"\"
        results = []
        for item in self.data:
            if 'value' in item and item['value'] > self.config.get('threshold', 0):
                results.append({
                    'id': item.get('id', ''),
                    'processed_value': item['value'] * self.config.get('multiplier', 1)
                })
        return results

# Example usage
processor = DataProcessor({'threshold': 10, 'multiplier': 2})
processor.load_from_file('data.json')
results = processor.process()
print(f"Processed {len(results)} items")""",
            "complex": """import asyncio
import aiohttp
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DataItem:
    \"\"\"Represents a data item to be processed.\"\"\"
    id: str
    value: float
    metadata: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataItem':
        \"\"\"Create a DataItem from a dictionary.\"\"\"
        return cls(
            id=data.get('id', ''),
            value=float(data.get('value', 0)),
            metadata=data.get('metadata', {})
        )

class DataSource(ABC):
    \"\"\"Abstract base class for data sources.\"\"\"
    
    @abstractmethod
    async def fetch_data(self) -> List[DataItem]:
        \"\"\"Fetch data from the source.\"\"\"
        pass

class FileDataSource(DataSource):
    \"\"\"Data source that reads from a file.\"\"\"
    
    def __init__(self, filename: str):
        self.filename = filename
    
    async def fetch_data(self) -> List[DataItem]:
        \"\"\"Fetch data from a JSON file.\"\"\"
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
            return [DataItem.from_dict(item) for item in data]
        except Exception as e:
            logger.error(f"Error loading file {self.filename}: {e}")
            return []

class ApiDataSource(DataSource):
    \"\"\"Data source that fetches from an API.\"\"\"
    
    def __init__(self, api_url: str, headers: Optional[Dict[str, str]] = None):
        self.api_url = api_url
        self.headers = headers or {}
    
    async def fetch_data(self) -> List[DataItem]:
        \"\"\"Fetch data from an API endpoint.\"\"\"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [DataItem.from_dict(item) for item in data]
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching data from API {self.api_url}: {e}")
            return []

class DataProcessor:
    \"\"\"Process data from various sources.\"\"\"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sources: List[DataSource] = []
    
    def add_source(self, source: DataSource) -> None:
        \"\"\"Add a data source to the processor.\"\"\"
        self.sources.append(source)
    
    async def collect_data(self) -> List[DataItem]:
        \"\"\"Collect data from all sources.\"\"\"
        all_data = []
        for source in self.sources:
            data = await source.fetch_data()
            all_data.extend(data)
        return all_data
    
    async def process(self) -> Dict[str, Any]:
        \"\"\"Process the collected data.\"\"\"
        data = await self.collect_data()
        logger.info(f"Processing {len(data)} items")
        
        # Filter items based on threshold
        threshold = self.config.get('threshold', 0)
        filtered_data = [item for item in data if item.value > threshold]
        
        # Apply transformations
        multiplier = self.config.get('multiplier', 1)
        processed_items = []
        for item in filtered_data:
            processed_value = item.value * multiplier
            processed_items.append({
                'id': item.id,
                'original_value': item.value,
                'processed_value': processed_value,
                'metadata': item.metadata
            })
        
        # Generate summary
        total_original = sum(item.value for item in filtered_data)
        total_processed = sum(item['processed_value'] for item in processed_items)
        
        return {
            'items': processed_items,
            'summary': {
                'total_items': len(processed_items),
                'total_original_value': total_original,
                'total_processed_value': total_processed,
                'average_value': total_processed / len(processed_items) if processed_items else 0
            }
        }

async def main():
    \"\"\"Main function to demonstrate the data processor.\"\"\"
    # Create processor with configuration
    processor = DataProcessor({
        'threshold': 10,
        'multiplier': 2.5
    })
    
    # Add data sources
    processor.add_source(FileDataSource('data.json'))
    processor.add_source(ApiDataSource('https://api.example.com/data', {'Authorization': 'Bearer token'}))
    
    # Process data
    result = await processor.process()
    
    # Output results
    print(f"Processed {result['summary']['total_items']} items")
    print(f"Total original value: {result['summary']['total_original_value']:.2f}")
    print(f"Total processed value: {result['summary']['total_processed_value']:.2f}")
    print(f"Average value: {result['summary']['average_value']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())"""
        },
        "JavaScript": {
            "simple": """function addNumbers(a, b) {
  // Add two numbers and return the result
  return a + b;
}

// Example usage
const result = addNumbers(5, 10);
console.log(`The result is: ${result}`);""",
            "medium": """// Data processor module
class DataProcessor {
  constructor(config) {
    this.config = config;
    this.data = [];
  }

  loadFromFile(filename) {
    try {
      // In a browser environment, this would use fetch or XMLHttpRequest
      const fs = require('fs');
      const fileData = fs.readFileSync(filename, 'utf8');
      this.data = JSON.parse(fileData);
      return true;
    } catch (error) {
      console.error(`Error loading file: ${error.message}`);
      return false;
    }
  }

  process() {
    const results = [];
    for (const item of this.data) {
      if (item.value && item.value > this.config.threshold) {
        results.push({
          id: item.id || '',
          processedValue: item.value * this.config.multiplier
        });
      }
    }
    return results;
  }
}

// Example usage
const processor = new DataProcessor({ threshold: 10, multiplier: 2 });
processor.loadFromFile('data.json');
const results = processor.process();
console.log(`Processed ${results.length} items`);""",
            "complex": """import { fetchData } from './api-client.js';

/**
 * @typedef {Object} DataItem
 * @property {string} id - Unique identifier
 * @property {number} value - Numerical value
 * @property {Object} metadata - Additional information
 */

/**
 * Abstract base class for data sources
 * @abstract
 */
class DataSource {
  /**
   * Fetch data from the source
   * @returns {Promise<DataItem[]>} Array of data items
   */
  async fetchData() {
    throw new Error('Method not implemented');
  }
}

/**
 * Data source that fetches from an API
 * @extends DataSource
 */
class ApiDataSource extends DataSource {
  /**
   * @param {string} apiUrl - The API endpoint URL
   * @param {Object} headers - HTTP headers
   */
  constructor(apiUrl, headers = {}) {
    super();
    this.apiUrl = apiUrl;
    this.headers = headers;
  }

  /**
   * Fetch data from an API endpoint
   * @returns {Promise<DataItem[]>} Array of data items
   */
  async fetchData() {
    try {
      const response = await fetch(this.apiUrl, {
        method: 'GET',
        headers: this.headers
      });

      if (!response.ok) {
        console.error(`API request failed with status ${response.status}`);
        return [];
      }

      const data = await response.json();
      return data.map(item => ({
        id: item.id || '',
        value: Number(item.value) || 0,
        metadata: item.metadata || {}
      }));
    } catch (error) {
      console.error(`Error fetching data from API ${this.apiUrl}: ${error.message}`);
      return [];
    }
  }
}

/**
 * Data processor class to handle data from various sources
 */
class DataProcessor {
  /**
   * @param {Object} config - Configuration options
   */
  constructor(config) {
    this.config = config;
    this.sources = [];
    this.logger = config.logger || console;
  }

  /**
   * Add a data source to the processor
   * @param {DataSource} source - The data source to add
   */
  addSource(source) {
    if (!(source instanceof DataSource)) {
      throw new Error('Source must be an instance of DataSource');
    }
    this.sources.push(source);
  }

  /**
   * Collect data from all sources
   * @returns {Promise<DataItem[]>} Combined data from all sources
   */
  async collectData() {
    const allData = [];
    
    for (const source of this.sources) {
      try {
        const data = await source.fetchData();
        allData.push(...data);
      } catch (error) {
        this.logger.error(`Error collecting data: ${error.message}`);
      }
    }
    
    return allData;
  }

  /**
   * Process the collected data
   * @returns {Promise<Object>} Processed data and summary
   */
  async process() {
    const data = await this.collectData();
    this.logger.info(`Processing ${data.length} items`);
    
    // Filter items based on threshold
    const threshold = this.config.threshold || 0;
    const filteredData = data.filter(item => item.value > threshold);
    
    // Apply transformations
    const multiplier = this.config.multiplier || 1;
    const processedItems = filteredData.map(item => ({
      id: item.id,
      originalValue: item.value,
      processedValue: item.value * multiplier,
      metadata: item.metadata
    }));
    
    // Generate summary
    const totalOriginal = filteredData.reduce((sum, item) => sum + item.value, 0);
    const totalProcessed = processedItems.reduce((sum, item) => sum + item.processedValue, 0);
    const averageValue = processedItems.length ? totalProcessed / processedItems.length : 0;
    
    return {
      items: processedItems,
      summary: {
        totalItems: processedItems.length,
        totalOriginalValue: totalOriginal,
        totalProcessedValue: totalProcessed,
        averageValue: averageValue
      }
    };
  }
}

// Example usage
async function main() {
  // Create processor with configuration
  const processor = new DataProcessor({
    threshold: 10,
    multiplier: 2.5,
    logger: {
      info: (msg) => console.log(`[INFO] ${msg}`),
      error: (msg) => console.error(`[ERROR] ${msg}`)
    }
  });
  
  // Add data sources
  processor.addSource(new ApiDataSource('https://api.example.com/data', {
    'Authorization': 'Bearer token',
    'Content-Type': 'application/json'
  }));
  
  // Process data
  const result = await processor.process();
  
  // Output results
  console.log(`Processed ${result.summary.totalItems} items`);
  console.log(`Total original value: ${result.summary.totalOriginalValue.toFixed(2)}`);
  console.log(`Total processed value: ${result.summary.totalProcessedValue.toFixed(2)}`);
  console.log(`Average value: ${result.summary.averageValue.toFixed(2)}`);
}

// Run the main function
main().catch(error => {
  console.error(`Application error: ${error.message}`);
});"""
        }
    }
    
    # Default to Python if language not found
    if language not in language_code_examples:
        language = "Python"
    
    # Get example by complexity
    if complexity not in ["simple", "medium", "complex"]:
        complexity = "medium"
    
    return language_code_examples[language][complexity]

def generate_human_prompt(complexity: str = "medium") -> str:
    """Generate a realistic human prompt about programming."""
    language = random.choice(LANGUAGES)
    topic = random.choice(TOPICS)
    concept = random.choice(CONCEPTS)
    
    if complexity == "simple":
        templates = [
            f"How do I create a simple {concept} in {language}?",
            f"What's the best way to implement a {topic} in {language}?",
            f"Can you show me a basic {language} example for {topic}?",
            f"How do I use {random.choice(FRAMEWORKS.get(language, ['a library']))} in {language}?",
            f"I'm having trouble with a {language} {concept}. Can you help?"
        ]
    elif complexity == "medium":
        templates = [
            f"I need to create a {concept} in {language} that handles {topic} functionality. What's the best approach?",
            f"What's the most efficient way to implement {topic} using {language} and {random.choice(FRAMEWORKS.get(language, ['a framework']))}?",
            f"I'm working on a project using {language} and need to add {topic} features. How should I structure my {concept}?",
            f"Could you review this {language} code that implements a {concept} for {topic}? I think there might be a better way to structure it.",
            f"How can I optimize my {language} {concept} for better performance when dealing with {topic}?"
        ]
    else:  # complex
        templates = [
            f"I'm developing a complex system in {language} using {random.choice(FRAMEWORKS.get(language, ['a framework']))} that needs to handle high-volume {topic} operations. What's the best architectural approach for the {concept} layer?",
            f"What are the trade-offs between different {topic} implementation strategies in {language}? I'm specifically concerned about scalability and maintainability of our {concept} structure.",
            f"We're seeing performance issues in our {language} {concept} when dealing with large-scale {topic} operations. Can you suggest optimization strategies and potential architectural changes?",
            f"I need to refactor our {language} codebase to better handle {topic} complexity. The current {concept} design is causing issues with testability and extensibility. What patterns would you recommend?",
            f"Our team is building a distributed system in {language} that needs robust {topic} capabilities. How should we design our {concept} interfaces to ensure consistency and fault tolerance?"
        ]
    
    prompt = random.choice(templates)
    
    # Sometimes add code snippets for medium and complex prompts
    if complexity != "simple" and random.random() < 0.6:
        prompt += "\n\nHere's what I have so far:\n\n```\n"
        prompt += generate_code_example(language, "simple" if complexity == "medium" else "medium")
        prompt += "\n```\n\nCan you suggest improvements or a better approach?"
    
    return prompt

def generate_llm_response(prompt: str, complexity: str = "medium") -> str:
    """Generate a realistic LLM response to a programming question."""
    # Extract language from the prompt if possible
    language = None
    for lang in LANGUAGES:
        if lang in prompt:
            language = lang
            break
    
    if not language:
        language = random.choice(LANGUAGES)
    
    # Extract topic if possible
    topic = None
    for t in TOPICS:
        if t in prompt:
            topic = t
            break
    
    if not topic:
        topic = random.choice(TOPICS)
    
    # Generate response based on complexity
    response = ""
    
    if complexity == "simple":
        response = f"You can implement this in {language} using a simple approach:\n\n"
        response += f"```{language.lower()}\n"
        response += generate_code_example(language, "simple")
        response += "\n```\n\n"
        response += f"This creates a basic implementation for your {topic} functionality."
    
    elif complexity == "medium":
        response = f"For your {topic} implementation in {language}, I recommend structuring your code as follows:\n\n"
        response += f"```{language.lower()}\n"
        response += generate_code_example(language, "medium")
        response += "\n```\n\n"
        response += f"This approach gives you a good balance of flexibility and maintainability. The key points are:\n\n"
        response += f"1. Clear separation of concerns for your {topic} logic\n"
        response += f"2. Error handling to make your code robust\n"
        response += f"3. Configuration options to make the implementation adaptable\n\n"
        response += f"You could extend this by adding more validation or enhancing the error handling."
    
    else:  # complex
        response = f"For a robust {topic} system in {language}, you'll want to consider several architectural aspects:\n\n"
        response += "**1. Architecture**\n\n"
        response += f"I recommend using a layered architecture with clear separation of concerns. Here's a comprehensive implementation:\n\n"
        response += f"```{language.lower()}\n"
        response += generate_code_example(language, "complex")
        response += "\n```\n\n"
        response += "**2. Key Design Considerations**\n\n"
        response += f"- **Abstraction**: The use of abstract classes provides flexibility for different {topic} sources\n"
        response += "- **Error Handling**: Comprehensive error handling at each layer ensures robustness\n"
        response += "- **Configuration**: Externalized configuration makes the system adaptable\n"
        response += "- **Performance**: Optimized processing with early filtering and efficient data structures\n\n"
        response += "**3. Further Enhancements**\n\n"
        response += "You could further improve this implementation by:\n"
        response += "- Adding caching mechanisms for frequently accessed data\n"
        response += "- Implementing retry logic for transient failures\n"
        response += "- Adding telemetry and observability hooks\n"
        response += "- Implementing pagination for large datasets\n\n"
        response += "The implementation follows best practices for maintainability and scalability while addressing your specific requirements."
    
    return response

def generate_conversation(num_exchanges: int = 3, complexity: str = "medium") -> List[Dict[str, str]]:
    """Generate a full conversation with multiple exchanges."""
    conversation = []
    
    # Initialize with a human prompt
    human_prompt = generate_human_prompt(complexity)
    llm_response = generate_llm_response(human_prompt, complexity)
    
    conversation.append({
        "role": "human",
        "message": human_prompt,
        "timestamp": generate_timestamp()
    })
    
    conversation.append({
        "role": "llm",
        "message": llm_response,
        "timestamp": generate_timestamp()
    })
    
    # Generate follow-up exchanges
    for _ in range(num_exchanges - 1):
        # Create follow-up based on previous exchanges
        prev_topic = None
        for lang in LANGUAGES:
            if lang in llm_response:
                prev_topic = lang
                break
        
        if not prev_topic:
            for topic in TOPICS:
                if topic in llm_response:
                    prev_topic = topic
                    break
        
        # Generate follow-up question
        if prev_topic and random.random() < 0.7:
            follow_up = f"Thanks! Can you explain how I would {random.choice(['test', 'extend', 'optimize', 'deploy'])} this {prev_topic} implementation?"
        else:
            follow_up = f"That's helpful. What about handling {random.choice(['error cases', 'edge conditions', 'large datasets', 'security concerns'])}?"
        
        # Add some details sometimes
        if random.random() < 0.5:
            follow_up += f" I'm particularly interested in {random.choice(['performance', 'maintainability', 'scalability', 'security'])}."
        
        conversation.append({
            "role": "human",
            "message": follow_up,
            "timestamp": generate_timestamp()
        })
        
        # Generate LLM response to the follow-up
        follow_up_response = generate_llm_response(follow_up, complexity)
        conversation.append({
            "role": "llm",
            "message": follow_up_response,
            "timestamp": generate_timestamp()
        })
        
        # Update the last response for next iteration
        llm_response = follow_up_response
    
    return conversation

def format_conversation_to_markdown(conversation: List[Dict[str, str]], session_id: int) -> str:
    """Format a conversation into markdown format."""
    markdown = f"## Session {session_id}\n\n"
    
    for i, message in enumerate(conversation):
        if message["role"] == "human":
            markdown += f"### Human (Message {i//2 + 1}) - {message['timestamp']}\n\n"
            markdown += f"{message['message']}\n\n"
        else:
            markdown += f"### LLM Response - {message['timestamp']}\n\n"
            markdown += f"{message['message']}\n\n"
    
    return markdown

def generate_example_data(
    output_file: str, 
    num_conversations: int = 3,
    exchanges_per_conversation: int = 3,
    complexity: str = "medium"
) -> None:
    """Generate example data and write to the specified output file."""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    # Generate conversations
    all_md = "# Extracted Chat Sessions\n\n"
    
    for i in range(1, num_conversations + 1):
        # Vary complexity slightly for more realism
        conv_complexity = complexity
        if random.random() < 0.3:
            complexities = ["simple", "medium", "complex"]
            current_idx = complexities.index(complexity)
            possible_indices = [idx for idx in range(len(complexities)) if idx != current_idx]
            if possible_indices:
                conv_complexity = complexities[random.choice(possible_indices)]
        
        # Generate conversation
        conversation = generate_conversation(
            num_exchanges=exchanges_per_conversation,
            complexity=conv_complexity
        )
        
        # Format to markdown and add to result
        all_md += format_conversation_to_markdown(conversation, i)
        
        # Add separator between conversations
        if i < num_conversations:
            all_md += "---\n\n"
    
    # Write to output file
    with open(output_file, 'w') as f:
        f.write(all_md)
    
    print(f"Generated {num_conversations} example conversations with {exchanges_per_conversation} exchanges each")
    print(f"Output written to: {output_file}")

def main():
    """Main function to parse arguments and generate example data."""
    parser = argparse.ArgumentParser(description="Generate example chat data for demonstration purposes")
    parser.add_argument("--output", type=str, required=True, help="Output markdown file path")
    parser.add_argument("--conversations", type=int, default=3, help="Number of conversations to generate")
    parser.add_argument("--exchanges", type=int, default=3, help="Number of exchanges per conversation")
    parser.add_argument("--complexity", type=str, default="medium", choices=["simple", "medium", "complex"],
                        help="Complexity level of the generated conversations")
    
    args = parser.parse_args()
    
    generate_example_data(
        output_file=args.output,
        num_conversations=args.conversations,
        exchanges_per_conversation=args.exchanges,
        complexity=args.complexity
    )

if __name__ == "__main__":
    main() 