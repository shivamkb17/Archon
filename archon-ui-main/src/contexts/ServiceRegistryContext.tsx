/**
 * Service Registry Context
 * 
 * Provides dynamic loading of services and agents from the database
 * instead of static AGENT_CONFIGS definitions.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { serviceRegistryService, ServiceInfo } from '../services/serviceRegistryService';
import { useToast } from './ToastContext';

interface ServiceRegistryContextType {
  // Service data
  services: ServiceInfo[];
  agents: ServiceInfo[];
  backendServices: ServiceInfo[];
  
  // Loading states
  loading: boolean;
  error: string | null;
  
  // Methods
  refreshServices: () => Promise<void>;
  getServiceByName: (serviceName: string) => ServiceInfo | undefined;
  
  // Legacy compatibility helpers
  getAgentConfigs: () => Record<string, any>;
  getAgentsArray: () => any[];
  getServicesArray: () => any[];
}

const ServiceRegistryContext = createContext<ServiceRegistryContextType | null>(null);

export const useServiceRegistry = () => {
  const context = useContext(ServiceRegistryContext);
  if (!context) {
    throw new Error('useServiceRegistry must be used within ServiceRegistryProvider');
  }
  return context;
};

interface ServiceRegistryProviderProps {
  children: React.ReactNode;
}

export const ServiceRegistryProvider: React.FC<ServiceRegistryProviderProps> = ({ children }) => {
  const [services, setServices] = useState<ServiceInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { showToast } = useToast();

  // Derived state
  const agents = services.filter(s => s.category === 'agent');
  const backendServices = services.filter(s => s.category === 'service');

  const refreshServices = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all active services from database
      const allServices = await serviceRegistryService.getAllServices(true);
      setServices(allServices);

      console.log(`[ServiceRegistry] Loaded ${allServices.length} services from database`);
      console.log(`[ServiceRegistry] Agents: ${agents.length}, Services: ${backendServices.length}`);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load services';
      setError(errorMessage);
      console.error('[ServiceRegistry] Failed to load services:', err);
      
      // Show toast error, but don't fail completely
      showToast('Failed to load service registry - using fallback', 'warning');
      
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  // Load services on mount
  useEffect(() => {
    refreshServices();
  }, [refreshServices]);

  const getServiceByName = useCallback((serviceName: string): ServiceInfo | undefined => {
    return services.find(s => s.service_name === serviceName);
  }, [services]);

  // Legacy compatibility methods
  const getAgentConfigs = useCallback((): Record<string, any> => {
    const configs: Record<string, any> = {};
    
    for (const service of services) {
      configs[service.service_name] = {
        id: service.service_name,
        name: service.display_name,
        icon: service.icon || '🔧',
        description: service.description || '',
        category: service.category,
        supportsTemperature: service.supports_temperature,
        supportsMaxTokens: service.supports_max_tokens,
        defaultModel: service.default_model || 'openai:gpt-4o-mini',
        modelType: service.model_type,
        costProfile: service.cost_profile || 'medium'
      };
    }
    
    return configs;
  }, [services]);

  const getAgentsArray = useCallback((): any[] => {
    return agents.map(agent => ({
      id: agent.service_name,
      name: agent.display_name,
      icon: agent.icon || '🤖',
      description: agent.description || '',
      category: agent.category,
      supportsTemperature: agent.supports_temperature,
      supportsMaxTokens: agent.supports_max_tokens,
      defaultModel: agent.default_model || 'openai:gpt-4o-mini',
      modelType: agent.model_type,
      costProfile: agent.cost_profile || 'medium'
    }));
  }, [agents]);

  const getServicesArray = useCallback((): any[] => {
    return backendServices.map(service => ({
      id: service.service_name,
      name: service.display_name,
      icon: service.icon || '⚙️',
      description: service.description || '',
      category: service.category,
      supportsTemperature: service.supports_temperature,
      supportsMaxTokens: service.supports_max_tokens,
      defaultModel: service.default_model || 'openai:gpt-4o-mini',
      modelType: service.model_type,
      costProfile: service.cost_profile || 'medium'
    }));
  }, [backendServices]);

  const value: ServiceRegistryContextType = {
    services,
    agents,
    backendServices,
    loading,
    error,
    refreshServices,
    getServiceByName,
    getAgentConfigs,
    getAgentsArray,
    getServicesArray
  };

  return (
    <ServiceRegistryContext.Provider value={value}>
      {children}
    </ServiceRegistryContext.Provider>
  );
};