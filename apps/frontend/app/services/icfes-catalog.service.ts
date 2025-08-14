import api from '@/lib/axios';

export interface ICFESTopic {
  code: string;
  area: string;
  main_topic: string;
  suggested_channel: string;
  youtube_url: string;
  youtube_video_id: string;
  difficulty: number;
  icfes_weight: number;
  estimated_time: number;
}

export interface ICFESArea {
  code: string;
  name: string;
  topic_count: number;
  total_weight: number;
  estimated_total_time: number;
}

export interface ICFESVideo {
  topic_code: string;
  topic_name: string;
  youtube_url: string;
  video_id: string;
  channel: string;
}

export interface ICFESRecommendation {
  user_level: number;
  recommended_topics: ICFESTopic[];
  total_recommended: number;
}

export interface ICFESStatistics {
  total_areas: number;
  total_topics: number;
  total_videos: number;
  areas_breakdown: Record<string, {
    topic_count: number;
    video_count: number;
    total_weight: number;
    estimated_time: number;
  }>;
}

export interface ICFESSearchResult {
  query: string;
  results: ICFESTopic[];
  total_results: number;
  filters: {
    area_code?: string;
    difficulty?: number;
  };
}

class ICFESCatalogService {
  private readonly baseUrl = '/api/v1/icfes-catalog';

  /**
   * Obtener todas las áreas disponibles del ICFES
   */
  async getAreas(): Promise<ICFESArea[]> {
    try {
      const response = await api.get(`${this.baseUrl}/areas`);
      return response.data.areas || [];
    } catch (error) {
      console.error('Error obteniendo áreas ICFES:', error);
      return [];
    }
  }

  /**
   * Obtener todos los temas de un área específica
   */
  async getTopicsByArea(
    areaCode: string, 
    difficulty?: number
  ): Promise<ICFESTopic[]> {
    try {
      const params = difficulty ? { difficulty } : {};
      const response = await api.get(`${this.baseUrl}/areas/${areaCode}/topics`, { params });
      return response.data.topics || [];
    } catch (error) {
      console.error(`Error obteniendo temas para área ${areaCode}:`, error);
      return [];
    }
  }

  /**
   * Obtener un tema específico por código
   */
  async getTopicByCode(topicCode: string): Promise<ICFESTopic | null> {
    try {
      const response = await api.get(`${this.baseUrl}/topics/${topicCode}`);
      return response.data.topic || null;
    } catch (error) {
      console.error(`Error obteniendo tema ${topicCode}:`, error);
      return null;
    }
  }

  /**
   * Obtener todos los videos YouTube de un área específica
   */
  async getYouTubeVideosByArea(areaCode: string): Promise<ICFESVideo[]> {
    try {
      const response = await api.get(`${this.baseUrl}/areas/${areaCode}/videos`);
      return response.data.videos || [];
    } catch (error) {
      console.error(`Error obteniendo videos para área ${areaCode}:`, error);
      return [];
    }
  }

  /**
   * Obtener temas recomendados basados en el nivel del usuario
   */
  async getRecommendedTopics(maxTopics: number = 10): Promise<ICFESRecommendation | null> {
    try {
      const response = await api.get(`${this.baseUrl}/recommendations`, {
        params: { max_topics: maxTopics }
      });
      return response.data || null;
    } catch (error) {
      console.error('Error obteniendo temas recomendados:', error);
      return null;
    }
  }

  /**
   * Generar unidades de estudio basadas en el catálogo ICFES
   */
  async generateStudyUnitsFromCatalog(areaCode: string): Promise<any> {
    try {
      const response = await api.post(`${this.baseUrl}/areas/${areaCode}/generate-units`);
      return response.data || null;
    } catch (error) {
      console.error(`Error generando unidades para área ${areaCode}:`, error);
      return null;
    }
  }

  /**
   * Obtener estadísticas completas del catálogo ICFES
   */
  async getCatalogStatistics(): Promise<ICFESStatistics | null> {
    try {
      const response = await api.get(`${this.baseUrl}/statistics`);
      return response.data.statistics || null;
    } catch (error) {
      console.error('Error obteniendo estadísticas del catálogo:', error);
      return null;
    }
  }

  /**
   * Buscar temas en el catálogo ICFES
   */
  async searchTopics(
    query: string, 
    areaCode?: string, 
    difficulty?: number
  ): Promise<ICFESSearchResult | null> {
    try {
      const params: any = { query };
      if (areaCode) params.area_code = areaCode;
      if (difficulty) params.difficulty = difficulty;

      const response = await api.get(`${this.baseUrl}/search`, { params });
      return response.data || null;
    } catch (error) {
      console.error('Error en búsqueda:', error);
      return null;
    }
  }

  /**
   * Obtener información completa de un área con sus temas
   */
  async getAreaWithTopics(areaCode: string): Promise<{
    area: ICFESArea;
    topics: ICFESTopic[];
    videos: ICFESVideo[];
  } | null> {
    try {
      const [areasResponse, topicsResponse, videosResponse] = await Promise.all([
        this.getAreas(),
        this.getTopicsByArea(areaCode),
        this.getYouTubeVideosByArea(areaCode)
      ]);

      const area = areasResponse.find(a => a.code === areaCode);
      if (!area) return null;

      return {
        area,
        topics: topicsResponse,
        videos: videosResponse
      };
    } catch (error) {
      console.error(`Error obteniendo información completa del área ${areaCode}:`, error);
      return null;
    }
  }

  /**
   * Obtener temas por nivel de dificultad
   */
  async getTopicsByDifficulty(areaCode: string, difficulty: number): Promise<ICFESTopic[]> {
    try {
      const allTopics = await this.getTopicsByArea(areaCode);
      return allTopics.filter(topic => topic.difficulty === difficulty);
    } catch (error) {
      console.error(`Error filtrando temas por dificultad ${difficulty}:`, error);
      return [];
    }
  }

  /**
   * Obtener temas más importantes por peso ICFES
   */
  async getTopTopicsByWeight(areaCode: string, limit: number = 10): Promise<ICFESTopic[]> {
    try {
      const allTopics = await this.getTopicsByArea(areaCode);
      return allTopics
        .sort((a, b) => b.icfes_weight - a.icfes_weight)
        .slice(0, limit);
    } catch (error) {
      console.error(`Error obteniendo temas top por peso para área ${areaCode}:`, error);
      return [];
    }
  }

  /**
   * Obtener tiempo total estimado para un área
   */
  async getEstimatedTimeForArea(areaCode: string): Promise<number> {
    try {
      const topics = await this.getTopicsByArea(areaCode);
      return topics.reduce((total, topic) => total + topic.estimated_time, 0);
    } catch (error) {
      console.error(`Error calculando tiempo estimado para área ${areaCode}:`, error);
      return 0;
    }
  }

  /**
   * Obtener peso total ICFES para un área
   */
  async getTotalWeightForArea(areaCode: string): Promise<number> {
    try {
      const topics = await this.getTopicsByArea(areaCode);
      return topics.reduce((total, topic) => total + topic.icfes_weight, 0);
    } catch (error) {
      console.error(`Error calculando peso total para área ${areaCode}:`, error);
      return 0;
    }
  }

  /**
   * Verificar si un área tiene videos disponibles
   */
  async hasVideos(areaCode: string): Promise<boolean> {
    try {
      const videos = await this.getYouTubeVideosByArea(areaCode);
      return videos.length > 0;
    } catch (error) {
      console.error(`Error verificando videos para área ${areaCode}:`, error);
      return false;
    }
  }

  /**
   * Obtener canales de YouTube más populares
   */
  async getPopularChannels(): Promise<string[]> {
    try {
      const areas = await this.getAreas();
      const allTopics: ICFESTopic[] = [];
      
      for (const area of areas) {
        const topics = await this.getTopicsByArea(area.code);
        allTopics.push(...topics);
      }

      const channelCounts: Record<string, number> = {};
      allTopics.forEach(topic => {
        if (topic.suggested_channel) {
          channelCounts[topic.suggested_channel] = (channelCounts[topic.suggested_channel] || 0) + 1;
        }
      });

      return Object.entries(channelCounts)
        .sort(([, a], [, b]) => b - a)
        .map(([channel]) => channel)
        .slice(0, 10);
    } catch (error) {
      console.error('Error obteniendo canales populares:', error);
      return [];
    }
  }
}

export const icfesCatalogService = new ICFESCatalogService();
