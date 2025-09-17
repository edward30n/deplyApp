import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Hook genérico para obtener datos
export const useData = (endpoint: string) => {
  return useQuery({
    queryKey: [endpoint],
    queryFn: () => fetch(`/api/v1/${endpoint}`).then(res => res.json()),
  });
};

// Hook genérico para crear elementos
export const useCreateItem = (endpoint: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: any) => 
      fetch(`/api/v1/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }).then(res => res.json()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [endpoint] });
    },
  });
};

// Hook genérico para actualizar elementos
export const useUpdateItem = (endpoint: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      fetch(`/api/v1/${endpoint}/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }).then(res => res.json()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [endpoint] });
    },
  });
};

// Hook genérico para eliminar elementos
export const useDeleteItem = (endpoint: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) =>
      fetch(`/api/v1/${endpoint}/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [endpoint] });
    },
  });
};
