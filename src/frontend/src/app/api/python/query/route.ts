import { NextRequest, NextResponse } from 'next/server'

// Enhanced logging utility
function logDebugInfo(context: string, data: unknown) {
  if (process.env.NODE_ENV === 'development' || process.env.DEBUG === 'true') {
    console.log(`🔍 [PYTHON_MOCK] ${context}`, JSON.stringify(data, null, 2))
  }
}

export async function POST(request: NextRequest) {
  const startTime = Date.now()
  
  try {
    const body = await request.json()
    logDebugInfo('REQUEST_BODY', body)
    
    // Dynamic mock response based on query - simulates what the Python function would return
    const query = body.query.toLowerCase()
    
    let mockResponse: {
      answer: string
      chunks: Array<{
        document: string
        metadata: {
          document_name: string
          page_in_document: number
          page_approximation: boolean
        }
      }>
      sources: string[]
    }
    
    if (query.includes('circularity gap')) {
      mockResponse = {
        answer: "The circularity gap refers to the difference between the amount of materials that are actually recycled and reused in the economy versus the total amount of materials consumed. It represents the percentage of materials that are lost from the economy after a single use, highlighting the inefficiency of our current linear economic model.",
        chunks: [
          {
            document: "The circularity gap is a key metric in circular economy analysis. It measures the percentage of materials that are lost from the economy after a single use, highlighting the inefficiency of our current linear economic model.",
            metadata: {
              document_name: "Circularity Gap Report 2021",
              page_in_document: 15,
              page_approximation: false
            }
          },
          {
            document: "Materials that are not recovered represent a significant economic and environmental loss. The circularity gap shows us exactly how much value we're losing through our current consumption patterns.",
            metadata: {
              document_name: "Circularity Gap Report 2022", 
              page_in_document: 23,
              page_approximation: false
            }
          }
        ],
        sources: [
          "Circularity Gap Report 2021",
          "Circularity Gap Report 2022"
        ]
      }
    } else if (query.includes('business model') || query.includes('circular business')) {
      mockResponse = {
        answer: "Circular business models are economic systems that eliminate waste and pollution, keep products and materials in use, and regenerate natural systems. They include models like product-as-a-service, sharing platforms, and resource recovery systems that create value while reducing environmental impact.",
        chunks: [
          {
            document: "Circular business models fundamentally change how companies create, deliver, and capture value. Instead of the traditional linear 'take-make-waste' approach, these models focus on resource efficiency and waste elimination.",
            metadata: {
              document_name: "The Circular Economy Handbook",
              page_in_document: 45,
              page_approximation: false
            }
          },
          {
            document: "Product-as-a-service models, where companies retain ownership of products and charge for their use, are a key example of circular business innovation. This approach incentivizes durability and resource efficiency.",
            metadata: {
              document_name: "Circular Business Models Guide",
              page_in_document: 78,
              page_approximation: false
            }
          }
        ],
        sources: [
          "The Circular Economy Handbook",
          "Circular Business Models Guide"
        ]
      }
    } else if (query.includes('sustainability') || query.includes('environment')) {
      mockResponse = {
        answer: "Sustainability in the circular economy context refers to meeting present needs without compromising the ability of future generations to meet their own needs. It encompasses environmental protection, social equity, and economic viability through circular practices.",
        chunks: [
          {
            document: "Sustainability requires a fundamental shift from linear to circular thinking. This means designing products and systems that minimize waste, maximize resource efficiency, and regenerate natural capital.",
            metadata: {
              document_name: "Sustainability and Circular Economy",
              page_in_document: 12,
              page_approximation: false
            }
          },
          {
            document: "Environmental sustainability in circular systems focuses on reducing carbon emissions, protecting biodiversity, and ensuring renewable resource use. Social sustainability ensures fair labor practices and community benefits.",
            metadata: {
              document_name: "Environmental Impact Assessment",
              page_in_document: 34,
              page_approximation: false
            }
          }
        ],
        sources: [
          "Sustainability and Circular Economy",
          "Environmental Impact Assessment"
        ]
      }
    } else {
      // Default response for other queries
      mockResponse = {
        answer: `Based on your query "${body.query}", I found relevant information about circular economy principles. The circular economy represents a systemic approach to economic development designed to benefit businesses, society, and the environment by keeping products, components, and materials at their highest utility and value at all times.`,
        chunks: [
          {
            document: "The circular economy is based on three principles: design out waste and pollution, keep products and materials in use, and regenerate natural systems. This approach creates a more sustainable and resilient economic model.",
            metadata: {
              document_name: "Circular Economy Principles",
              page_in_document: 8,
              page_approximation: false
            }
          },
          {
            document: "Transitioning to a circular economy requires collaboration across all sectors and stakeholders. It involves rethinking how we design products, manage resources, and create value in our economic systems.",
            metadata: {
              document_name: "Circular Economy Transition Guide",
              page_in_document: 22,
              page_approximation: false
            }
          }
        ],
        sources: [
          "Circular Economy Principles",
          "Circular Economy Transition Guide"
        ]
      }
    }
    
    const responseTime = Date.now() - startTime
    logDebugInfo('MOCK_RESPONSE', { 
      answerLength: mockResponse.answer.length,
      chunksCount: mockResponse.chunks.length,
      responseTime: `${responseTime}ms`
    })
    
    return NextResponse.json(mockResponse)
    
  } catch (error) {
    const responseTime = Date.now() - startTime
    logDebugInfo('EXCEPTION', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      responseTime: `${responseTime}ms`
    })
    
    return NextResponse.json(
      { detail: `Mock API error: ${error instanceof Error ? error.message : 'Unknown error'}` },
      { status: 500 }
    )
  }
}
