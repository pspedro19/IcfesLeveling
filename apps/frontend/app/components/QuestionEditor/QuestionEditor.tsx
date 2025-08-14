'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Save, 
  Eye, 
  EyeOff, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Image as ImageIcon,
  Trash2,
  Plus,
  Settings
} from 'lucide-react';
import { Question, QuestionCreate, QuestionUpdate, QuestionValidationRequest } from '@/types/question';
import { questionService } from '@/services/question.service';

interface QuestionEditorProps {
  question?: Question;
  onSave?: (question: Question) => void;
  onCancel?: () => void;
  mode?: 'create' | 'edit' | 'validate';
}

export default function QuestionEditor({ 
  question, 
  onSave, 
  onCancel, 
  mode = 'create' 
}: QuestionEditorProps) {
  const [formData, setFormData] = useState<Partial<QuestionCreate>>({
    question_text: '',
    difficulty: 5,
    correct_answer: '',
    options: { A: '', B: '', C: '', D: '' },
    explanation: '',
    hint: '',
    tags: [],
    image_url: '',
    options_images: {}
  });

  const [validation, setValidation] = useState<{
    isValid: boolean;
    errors: string[];
    warnings: string[];
    suggestions: string[];
  }>({
    isValid: false,
    errors: [],
    warnings: [],
    suggestions: []
  });

  const [isLoading, setIsLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showValidation, setShowValidation] = useState(false);

  useEffect(() => {
    if (question && mode === 'edit') {
      setFormData({
        question_text: question.question_text,
        difficulty: question.difficulty,
        correct_answer: question.correct_answer,
        options: question.options,
        explanation: question.explanation,
        hint: question.hint,
        tags: question.tags,
        image_url: question.image_url,
        options_images: question.options_images
      });
    }
  }, [question, mode]);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleOptionChange = (key: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      options: {
        ...prev.options,
        [key]: value
      }
    }));
  };

  const addOption = () => {
    const optionKeys = Object.keys(formData.options || {});
    const nextKey = String.fromCharCode(65 + optionKeys.length); // A, B, C, D, E, F
    
    if (optionKeys.length < 6) {
      setFormData(prev => ({
        ...prev,
        options: {
          ...prev.options,
          [nextKey]: ''
        }
      }));
    }
  };

  const removeOption = (key: string) => {
    const optionKeys = Object.keys(formData.options || {});
    if (optionKeys.length > 2) {
      setFormData(prev => {
        const newOptions = { ...prev.options };
        delete newOptions[key];
        
        // Update correct answer if it was the removed option
        let newCorrectAnswer = prev.correct_answer;
        if (prev.correct_answer === key) {
          newCorrectAnswer = Object.keys(newOptions)[0] || '';
        }
        
        return {
          ...prev,
          options: newOptions,
          correct_answer: newCorrectAnswer
        };
      });
    }
  };

  const validateQuestion = async () => {
    if (!formData.question_text || !formData.options || !formData.correct_answer) {
      return;
    }

    setIsLoading(true);
    try {
      const validationRequest: QuestionValidationRequest = {
        question_text: formData.question_text,
        options: formData.options,
        correct_answer: formData.correct_answer,
        image_url: formData.image_url,
        options_images: formData.options_images
      };

      const result = await questionService.validateQuestion(validationRequest);
      setValidation({
        isValid: result.is_valid,
        errors: result.errors,
        warnings: result.warnings,
        suggestions: result.suggestions
      });
      setShowValidation(true);
    } catch (error) {
      console.error('Validation error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!validation.isValid) {
      await validateQuestion();
      return;
    }

    setIsLoading(true);
    try {
      let savedQuestion: Question;

      if (mode === 'create') {
        savedQuestion = await questionService.createQuestion(formData as QuestionCreate);
      } else {
        savedQuestion = await questionService.updateQuestion(
          question!.id, 
          formData as QuestionUpdate
        );
      }

      onSave?.(savedQuestion);
    } catch (error) {
      console.error('Save error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getValidationIcon = () => {
    if (validation.errors.length > 0) {
      return <XCircle className="w-5 h-5 text-red-500" />;
    } else if (validation.warnings.length > 0) {
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    } else if (validation.isValid) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
    return <Settings className="w-5 h-5 text-gray-500" />;
  };

  return (
    <div className="bg-gray-900/90 rounded-lg p-6 border border-purple-500/30">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">
          {mode === 'create' ? 'Crear Pregunta' : 'Editar Pregunta'}
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition-all"
          >
            {showPreview ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
          <button
            onClick={validateQuestion}
            disabled={isLoading}
            className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white transition-all disabled:opacity-50"
          >
            {getValidationIcon()}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form */}
        <div className="space-y-4">
          {/* Question Text */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Pregunta *
            </label>
            <textarea
              value={formData.question_text}
              onChange={(e) => handleInputChange('question_text', e.target.value)}
              className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
              rows={4}
              placeholder="Escribe la pregunta aquí..."
            />
          </div>

          {/* Difficulty */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Dificultad: {formData.difficulty}/10
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={formData.difficulty}
              onChange={(e) => handleInputChange('difficulty', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
            />
          </div>

          {/* Options */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Opciones *
            </label>
            <div className="space-y-2">
              {Object.entries(formData.options || {}).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="correct_answer"
                    value={key}
                    checked={formData.correct_answer === key}
                    onChange={(e) => handleInputChange('correct_answer', e.target.value)}
                    className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 focus:ring-purple-500"
                  />
                  <span className="w-8 text-center text-gray-300 font-bold">{key}</span>
                  <input
                    type="text"
                    value={value}
                    onChange={(e) => handleOptionChange(key, e.target.value)}
                    className="flex-1 p-2 bg-gray-800 border border-gray-600 rounded text-white placeholder-gray-400 focus:border-purple-500"
                    placeholder={`Opción ${key}`}
                  />
                  {Object.keys(formData.options || {}).length > 2 && (
                    <button
                      onClick={() => removeOption(key)}
                      className="p-2 text-red-400 hover:text-red-300 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
              {Object.keys(formData.options || {}).length < 6 && (
                <button
                  onClick={addOption}
                  className="flex items-center gap-2 text-purple-400 hover:text-purple-300 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Agregar opción
                </button>
              )}
            </div>
          </div>

          {/* Explanation */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Explicación
            </label>
            <textarea
              value={formData.explanation}
              onChange={(e) => handleInputChange('explanation', e.target.value)}
              className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-purple-500"
              rows={3}
              placeholder="Explicación de la respuesta correcta..."
            />
          </div>

          {/* Hint */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Pista
            </label>
            <input
              type="text"
              value={formData.hint}
              onChange={(e) => handleInputChange('hint', e.target.value)}
              className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-purple-500"
              placeholder="Pista para ayudar al estudiante..."
            />
          </div>
        </div>

        {/* Preview */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Vista Previa</h3>
          
          {showPreview && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-800 rounded-lg p-4 border border-gray-600"
            >
              <div className="mb-4">
                <div className="flex items-center gap-2 text-gray-400 mb-2">
                  <span>Dificultad: {formData.difficulty}/10</span>
                </div>
                <h4 className="text-white font-medium mb-4">
                  {formData.question_text || 'Pregunta de ejemplo...'}
                </h4>
              </div>

              <div className="space-y-2">
                {Object.entries(formData.options || {}).map(([key, value]) => (
                  <div
                    key={key}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      formData.correct_answer === key
                        ? 'border-green-500 bg-green-500/10'
                        : 'border-gray-600 bg-gray-700/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold ${
                        formData.correct_answer === key
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-600 text-gray-300'
                      }`}>
                        {key}
                      </div>
                      <span className="text-gray-300">
                        {value || `Opción ${key}`}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {formData.explanation && (
                <div className="mt-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
                  <h5 className="font-semibold text-blue-300 mb-1">Explicación:</h5>
                  <p className="text-blue-200 text-sm">{formData.explanation}</p>
                </div>
              )}
            </motion.div>
          )}

          {/* Validation Results */}
          <AnimatePresence>
            {showValidation && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-3"
              >
                {validation.errors.length > 0 && (
                  <div className="p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                    <h5 className="font-semibold text-red-300 mb-2">Errores:</h5>
                    <ul className="text-red-200 text-sm space-y-1">
                      {validation.errors.map((error, index) => (
                        <li key={index}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {validation.warnings.length > 0 && (
                  <div className="p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
                    <h5 className="font-semibold text-yellow-300 mb-2">Advertencias:</h5>
                    <ul className="text-yellow-200 text-sm space-y-1">
                      {validation.warnings.map((warning, index) => (
                        <li key={index}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {validation.suggestions.length > 0 && (
                  <div className="p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
                    <h5 className="font-semibold text-blue-300 mb-2">Sugerencias:</h5>
                    <ul className="text-blue-200 text-sm space-y-1">
                      {validation.suggestions.map((suggestion, index) => (
                        <li key={index}>• {suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 mt-6 pt-6 border-t border-gray-700">
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-all"
        >
          Cancelar
        </button>
        <button
          onClick={handleSave}
          disabled={isLoading || !validation.isValid}
          className="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-all flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {isLoading ? 'Guardando...' : 'Guardar'}
        </button>
      </div>
    </div>
  );
} 