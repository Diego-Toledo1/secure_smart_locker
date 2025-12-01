import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, User, ShieldCheck } from 'lucide-react';
import axios from 'axios';

// URL de tu API Gateway (Ajústala con la de tu lista maestra)
const API_URL = "https://ogr7f6hfxd.execute-api.us-east-2.amazonaws.com/dev"; 

const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', name: '' });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Validaciones de seguridad
  const validateForm = () => {
    if (formData.password.length < 6) return "La contraseña debe tener mínimo 6 caracteres.";
    
    // Regex estricto para utez.edu.mx o gmail.com
    const emailRegex = /^[a-zA-Z0-9._%+-]+@(utez\.edu\.mx|gmail\.com)$/;
    if (!emailRegex.test(formData.email)) return "Correo invalido, favor de poner una dirreción valida.";
    
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const payload = isLogin 
        ? { email: formData.email, password: formData.password }
        : formData;

      const response = await axios.post(`${API_URL}${endpoint}`, payload);
      
      if (response.status === 200 || response.status === 201) {
        // Guardar token y rol (Simulado por ahora con la respuesta de la API)
        const userData = response.data.user || {};
        localStorage.setItem('token', response.data.token);
        localStorage.setItem('role', userData.role);
        
        // Protección: Reemplazar historial para no volver atrás
        if (userData.role === 'user') {
            navigate('/dashboard', { replace: true });
        } else {
            alert("Este portal es solo para usuarios. Usa el portal de Admin.");
        }
      }
    } catch (err) {
      setError(err.response?.data?.message || "Error de conexión");
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden">
      
      {/* IZQUIERDA: Branding (Negro/Naranja) */}
      <div className="hidden w-1/2 bg-locker-black-surface lg:flex flex-col justify-center items-center relative p-12 text-center border-r border-locker-black-border">
        <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-locker-orange to-red-600"></div>
        
        <div className="z-10">
          <div className="mb-6 inline-flex p-4 rounded-full bg-locker-black border border-locker-orange shadow-[0_0_20px_rgba(255,107,0,0.3)]">
            <Lock size={64} className="text-locker-orange" />
          </div>
          <h1 className="text-5xl font-bold text-white mb-2 tracking-tighter">
            SECURE <span className="text-locker-orange">SMART</span> LOCKER
          </h1>
          <p className="text-gray-400 text-lg mt-4 max-w-md mx-auto">
            Sistema automatizado de resguardo seguro mediante OTP y validación biométrica simulada.
          </p>
        </div>

        <div className="absolute bottom-10 text-gray-500 text-sm">
          <p className="font-semibold text-locker-orange">INTEGRANTES</p>
          <p>Miranda Toledo Diego Eduardo</p>
          <p>Nateras Velazquez Roberto</p>
        </div>
        
        {/* Decoración de fondo */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-locker-orange opacity-5 blur-[120px] rounded-full"></div>
      </div>

      {/* DERECHA: Login/Registro */}
      <div className="w-full lg:w-1/2 bg-locker-black flex flex-col justify-center items-center p-8">
        <div className="w-full max-w-md">
          <h2 className="text-3xl font-bold text-white mb-2">
            {isLogin ? 'Iniciar Sesión' : 'Crear Cuenta'}
          </h2>
          <p className="text-gray-400 mb-8">
            {isLogin ? 'Ingresa tus credenciales institucionales' : 'Regístrate para asignar tu casillero'}
          </p>

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-500 text-red-200 rounded text-sm flex items-center gap-2">
              <ShieldCheck size={16} /> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Nombre Completo</label>
                <div className="relative">
                  <User className="absolute left-3 top-3 text-gray-500" size={18} />
                  <input 
                    type="text" 
                    placeholder="Tu nombre"
                    className="w-full bg-locker-black-surface border border-locker-black-border rounded-lg py-2.5 pl-10 pr-4 text-white focus:outline-none focus:border-locker-orange transition-colors"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Correo Institucional</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 text-gray-500" size={18} />
                <input 
                  type="email" 
                  placeholder="ejemplo@utez.edu.mx"
                  className="w-full bg-locker-black-surface border border-locker-black-border rounded-lg py-2.5 pl-10 pr-4 text-white focus:outline-none focus:border-locker-orange transition-colors"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Contraseña</label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 text-gray-500" size={18} />
                <input 
                  type="password" 
                  placeholder="••••••••"
                  className="w-full bg-locker-black-surface border border-locker-black-border rounded-lg py-2.5 pl-10 pr-4 text-white focus:outline-none focus:border-locker-orange transition-colors"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                />
              </div>
            </div>

            <button 
              type="submit" 
              className="w-full bg-locker-orange hover:bg-locker-orange-hover text-white font-bold py-3 rounded-lg transition-all transform active:scale-95 shadow-lg shadow-locker-orange/20 mt-6"
            >
              {isLogin ? 'Acceder al Sistema' : 'Registrarme'}
            </button>
          </form>

          <div className="mt-8 text-center text-sm text-gray-500">
            {isLogin ? '¿No tienes casillero?' : '¿Ya tienes cuenta?'}
            <button 
              onClick={() => { setIsLogin(!isLogin); setError(''); }}
              className="ml-2 text-locker-orange hover:text-white transition-colors font-medium"
            >
              {isLogin ? 'Crear cuenta' : 'Inicia sesión'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;