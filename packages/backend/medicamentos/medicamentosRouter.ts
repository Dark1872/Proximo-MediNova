import { Router } from 'express';
import { getAll, getById, create, update, remove } from './medicamentosController.js';
import { requireAdmin } from '../shared/authMiddleware.js';

const router = Router();

// Consultas públicas (catálogo de medicamentos)
router.get('/', getAll);
router.get('/:id', getById);

// Operaciones administrativas restringidas
router.post('/', requireAdmin, create);
router.put('/:id', requireAdmin, update);
router.delete('/:id', requireAdmin, remove);

export default router;
