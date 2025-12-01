import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { LogOut, Box, User, Grid, Key, RefreshCw } from 'lucide-react';

const API_URL = "https://ogr7f6hfxd.execute-api.us-east-2.amazonaws.com/prod"; 

const Dashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState({ name: '', email: '', id: 1 }); // Estado del usuario
  const [hasLocker, setHasLocker] = useState(false);
  const [availableLockers, setAvailableLockers] = useState([]);
  const [myLockerData, setMyLockerData] = useState(null);
  const [currentOtp, setCurrentOtp] = useState('----');
  
  const [currentView, setCurrentView] = useState('grid'); 
  const [selectedLocker, setSelectedLocker] = useState(null);
  const [assignForm, setAssignForm] = useState({ days: 1, color: '#FF6B00' });

  useEffect(() => {
    // 1. Cargar datos del usuario guardados en Login
    const token = localStorage.getItem('token');
    const storedName = localStorage.getItem('userName');
    const storedEmail = localStorage.getItem('userEmail');
    const storedId = localStorage.getItem('userId') || 1; // Fallback a 1 para pruebas

    if (!token) navigate('/login');

    setUser({
        name: storedName || 'Usuario',
        email: storedEmail || 'correo@utez.edu.mx',
        id: storedId
    });
    
    fetchInitialData(storedId);
  }, []);

  // Lógica de Refresco de OTP (Solo si estamos en la vista OTP y tiene locker)
  useEffect(() => {
    let interval;
    if (hasLocker && currentView === 'otp') {
        // Llamada inmediata
        fetchNewOtp();
        // Intervalo de 15s
        interval = setInterval(fetchNewOtp, 15000);
    }
    return () => clearInterval(interval);
  }, [hasLocker, currentView]);

  const fetchNewOtp = async () => {
    // Validación de seguridad para no llamar sin ID
    if (!user || !user.id) return; 

    try {
        console.log("Refrescando OTP..."); // Para ver en consola F12
        const res = await axios.post(`${API_URL}/lockers/my-locker/otp/refresh`, { user_id: user.id });
        
        if (res.status === 200) {
            setCurrentOtp(res.data.otp);
        }
    } catch (error) {
        console.error("Error refrescando OTP:", error);
    }
  };

  const fetchInitialData = async (userId) => {
    setLoading(true);
    try {
      const myLockerRes = await axios.get(`${API_URL}/lockers/my-locker?user_id=${userId}`);
      if (myLockerRes.status === 200) {
        setHasLocker(true);
        setMyLockerData(myLockerRes.data);
        setCurrentView('otp'); 
      }
    } catch (error) {
      if (error.response && error.response.status === 404) {
        setHasLocker(false);
        setCurrentView('grid');
        loadAvailableLockers();
      }
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableLockers = async () => {
    try {
        const res = await axios.get(`${API_URL}/lockers/available`);
        setAvailableLockers(res.data);
    } catch (error) {
        console.error("Error cargando lockers", error);
    }
  };

  const handleAssign = async (e) => {
    e.preventDefault();
    if (!selectedLocker) return;
    try {
        const payload = { user_id: user.id, locker_id: selectedLocker.id, days: assignForm.days, color: assignForm.color };
        const res = await axios.post(`${API_URL}/lockers/assign`, payload);
        if(res.status === 200) {
            alert(`¡Asignado!`);
            window.location.reload();
        }
    } catch (err) {
        alert("Error al asignar: " + (err.response?.data?.message || err.message));
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login', { replace: true });
  };

  // --- NUEVAS FUNCIONES PARA PERFIL ---
  const handleCancelLocker = async () => {
    if (!hasLocker) return;
    
    // Confirmación simple
    if (!window.confirm("¿Estás seguro de que quieres cancelar tu locker? Esta acción liberará el espacio inmediatamente.")) {
      return;
    }

    try {
        // TU TAREA: Asegurar que este endpoint exista en tu LambdaLockerUserService
        const res = await axios.post(`${API_URL}/lockers/my-locker/request-cancel`, { user_id: user.id });
        
        if (res.status === 200) {
            alert("Locker cancelado exitosamente.");
            window.location.reload(); // Recargar para volver al selector
        }
    } catch (err) {
        console.error(err);
        alert("Error al cancelar: " + (err.response?.data?.message || "Revisa tu API"));
    }
  };

  const handleExtendRequest = async () => {
    if (!hasLocker) return;

    // Por ahora usaremos un prompt simple, luego puedes hacer un modal si quieres
    const dias = prompt("¿Cuántos días adicionales necesitas?", "1");
    if (!dias) return;

    try {
        // TU TAREA: Asegurar que este endpoint exista en tu LambdaLockerUserService
        const res = await axios.post(`${API_URL}/lockers/my-locker/request-time-change`, { 
            user_id: user.id,
            days: parseInt(dias) 
        });
        
        if (res.status === 200) {
            alert("Solicitud de tiempo enviada correctamente.");
        }
    } catch (err) {
        console.error(err);
        alert("Error al solicitar tiempo: " + (err.response?.data?.message || "Revisa tu API"));
    }
  };
  // ------------------------------------

  const renderContent = () => {
    switch (currentView) {
        case 'profile':
            return (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-8 animate-fade-in px-6">
                    {/* AVATAR */}
                    <div className="relative">
                        <div className="w-28 h-28 bg-locker-black-surface border-2 border-locker-orange rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(255,107,0,0.2)]">
                            <User size={56} className="text-locker-orange" />
                        </div>
                        {hasLocker && (
                            <div className="absolute bottom-0 right-0 w-8 h-8 bg-green-500 rounded-full border-4 border-locker-black flex items-center justify-center" title="Locker Activo">
                                <Key size={14} className="text-black" />
                            </div>
                        )}
                    </div>

                    {/* DATOS DEL USUARIO */}
                    <div className="space-y-1">
                        <h2 className="text-3xl font-bold text-white tracking-tight">{user.name}</h2>
                        <p className="text-gray-500 font-mono text-sm">{user.email}</p>
                    </div>

                    {/* TARJETA DE ESTADO */}
                    <div className="p-6 bg-locker-black-surface rounded-2xl border border-locker-black-border w-full max-w-sm space-y-4">
                        <div className="flex justify-between items-center border-b border-gray-800 pb-3">
                            <span className="text-sm text-gray-400">ID de Usuario</span>
                            <span className="text-sm font-mono text-white bg-white/5 px-2 py-1 rounded">{user.id}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-400">Estado del Servicio</span>
                            <span className={`text-xs font-bold px-3 py-1 rounded-full ${hasLocker ? 'bg-green-500/10 text-green-500' : 'bg-gray-700/30 text-gray-400'}`}>
                                {hasLocker ? 'ACTIVO' : 'INACTIVO'}
                            </span>
                        </div>
                        
                        {/* INFORMACIÓN DEL LOCKER (SI TIENE) */}
                        {hasLocker && myLockerData && (
                            <div className="mt-4 pt-4 border-t border-gray-800">
                                <div className="flex justify-between text-sm mb-2">
                                    <span className="text-gray-400">Locker Actual</span>
                                    <span className="text-locker-orange font-bold">{myLockerData.code}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-400">Vence</span>
                                    <span className="text-white">{new Date(myLockerData.expires_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* BOTONES DE ACCIÓN (SOLO SI TIENE LOCKER) */}
                    {hasLocker && (
                        <div className="flex flex-col w-full max-w-sm gap-3">
                            <button 
                                onClick={handleExtendRequest}
                                className="w-full py-3 rounded-xl border border-locker-orange text-locker-orange hover:bg-locker-orange hover:text-white transition-all font-medium flex items-center justify-center gap-2"
                            >
                                <RefreshCw size={18} />
                                Solicitar Más Tiempo
                            </button>
                            
                            <button 
                                onClick={handleCancelLocker}
                                className="w-full py-3 rounded-xl bg-red-900/10 border border-red-900/50 text-red-500 hover:bg-red-900/30 transition-all font-medium flex items-center justify-center gap-2"
                            >
                                <LogOut size={18} className="rotate-180" />
                                Cancelar / Liberar Locker
                            </button>
                        </div>
                    )}
                </div>
            );

        case 'otp':
            if (!hasLocker) return <div className="text-center mt-20 text-gray-500">No tienes un locker asignado.</div>;
            return (
                <div className="h-full flex flex-col items-center justify-center space-y-8">
                    <motion.div 
                        key={currentOtp} // Animar cuando cambie el código
                        initial={{ scale: 0.9, opacity: 0.5 }} 
                        animate={{ scale: 1, opacity: 1 }}
                        className="w-80 h-80 rounded-3xl bg-locker-black-surface border-4 shadow-[0_0_50px_rgba(255,107,0,0.15)] flex flex-col items-center justify-center relative overflow-hidden"
                        style={{ borderColor: myLockerData?.color_hex || '#FF6B00' }}
                    >
                        <div className="absolute top-0 w-full h-1 bg-locker-orange animate-pulse"></div>
                        <h2 className="text-gray-400 text-sm tracking-widest uppercase mb-4">Tu Código de Acceso</h2>
                        
                        <h1 className="text-7xl font-mono font-bold text-white tracking-widest tabular-nums">
                           {currentOtp}
                        </h1>
                        
                        <div className="mt-6 flex items-center gap-2 text-locker-orange text-xs bg-locker-orange/10 px-3 py-1 rounded-full">
                            <RefreshCw size={12} className="animate-spin" />
                            Actualizando cada 15s...
                        </div>
                    </motion.div>

                    <div className="text-center">
                        <h2 className="text-3xl font-bold text-white mb-1">{myLockerData?.code}</h2>
                        <p className="text-gray-500 text-sm">Vence: {new Date(myLockerData?.expires_at).toLocaleDateString()}</p>
                    </div>
                </div>
            );

        case 'grid':
        default:
            // Bloqueo si ya tiene locker
            if (hasLocker) {
                return (
                    <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-50">
                        <div className="w-20 h-20 bg-locker-black-surface rounded-full flex items-center justify-center border border-locker-black-border mb-6">
                             <Box size={40} className="text-gray-600" />
                        </div>
                        <h2 className="text-xl text-white font-bold mb-2">Ya has seleccionado un locker</h2>
                        <p className="text-gray-500 text-sm max-w-xs mx-auto">
                            Para elegir otro, primero debes liberar tu locker actual desde la sección "Mi Acceso".
                        </p>
                    </div>
                );
            }

            return (
                <div className="h-full flex flex-col">
                    <header className="mb-8">
                        <h1 className="text-3xl font-bold">Elige tu <span className="text-locker-orange">Locker</span></h1>
                        <p className="text-gray-400">Selecciona una ubicación disponible</p>
                    </header>

                    <div className="flex-1 flex items-center justify-center relative">
                        <AnimatePresence>
                            {!selectedLocker ? (
                                /* VISTA DE GRID (CUADRÍCULA) */
                                <motion.div 
                                    initial={{ opacity: 0 }} 
                                    animate={{ opacity: 1 }} 
                                    exit={{ opacity: 0, scale: 0.5 }} 
                                    className="grid grid-cols-2 gap-4 w-full max-w-md overflow-y-auto max-h-[60vh] pr-2"
                                >
                                    {availableLockers.length === 0 && !loading && (
                                        <div className="col-span-2 text-center py-10 text-gray-500">
                                            No hay lockers disponibles o error de conexión.
                                        </div>
                                    )}
                                    
                                    {availableLockers.map((locker) => (
                                        <motion.button
                                            key={locker.id}
                                            whileHover={{ scale: 1.05 }}
                                            whileTap={{ scale: 0.95 }}
                                            onClick={() => setSelectedLocker(locker)}
                                            className="h-32 rounded-2xl border-2 border-locker-black-border bg-locker-black-surface hover:border-locker-orange cursor-pointer flex flex-col items-center justify-center group"
                                        >
                                            <Box size={32} className="text-gray-400 group-hover:text-white transition-colors" />
                                            <span className="mt-2 font-bold text-lg text-white">{locker.code}</span>
                                            <span className="text-[10px] uppercase tracking-wider mt-1 text-locker-orange font-bold">DISPONIBLE</span>
                                        </motion.button>
                                    ))}
                                </motion.div>
                            ) : (
                                /* VISTA DE ASIGNACIÓN (CON LOCKER VISUAL DERECHA) */
                                <motion.div 
                                    initial={{ scale: 0.8, opacity: 0 }} 
                                    animate={{ scale: 1, opacity: 1 }} 
                                    className="w-full max-w-5xl flex flex-col lg:flex-row gap-12 items-center justify-center p-4"
                                >
                                    {/* COLUMNA IZQUIERDA: FORMULARIO */}
                                    <div className="w-full lg:w-1/2 p-8 bg-locker-black-surface border border-locker-black-border rounded-3xl shadow-2xl">
                                        <div className="flex justify-between items-center mb-6">
                                            <h3 className="text-2xl font-bold">Configurar {selectedLocker.code}</h3>
                                            <div className="px-3 py-1 bg-locker-orange/20 text-locker-orange rounded-full text-xs font-bold border border-locker-orange/50">
                                                SELECCIONADO
                                            </div>
                                        </div>
                                        
                                        <form onSubmit={handleAssign} className="space-y-6">
                                            <div>
                                                <label className="text-sm text-gray-400 block mb-2">Tiempo de uso</label>
                                                <select 
                                                    className="w-full bg-black border border-gray-700 rounded-xl p-4 text-white focus:border-locker-orange focus:outline-none transition-colors"
                                                    value={assignForm.days}
                                                    onChange={(e) => setAssignForm({...assignForm, days: e.target.value})}
                                                >
                                                    <option value="1">1 Día</option>
                                                    <option value="4">4 Días</option>
                                                    <option value="7">1 Semana</option>
                                                    <option value="30">1 Mes</option>
                                                </select>
                                            </div>
                                            
                                            <div>
                                                <label className="text-sm text-gray-400 block mb-2">Personalizar Color LED</label>
                                                <div className="flex items-center gap-4">
                                                    <input 
                                                        type="color" 
                                                        className="w-16 h-16 rounded-xl cursor-pointer border-none bg-transparent"
                                                        value={assignForm.color}
                                                        onChange={(e) => setAssignForm({...assignForm, color: e.target.value})}
                                                    />
                                                    <span className="text-xs text-gray-500">Toca el cuadro para cambiar el color del anillo LED.</span>
                                                </div>
                                            </div>

                                            <div className="flex gap-4 pt-4">
                                                <button 
                                                    type="button" 
                                                    onClick={() => setSelectedLocker(null)} 
                                                    className="flex-1 py-4 rounded-xl border border-gray-700 text-gray-400 hover:bg-gray-800 font-medium transition-colors"
                                                >
                                                    Cancelar
                                                </button>
                                                <button 
                                                    type="submit" 
                                                    className="flex-1 py-4 rounded-xl bg-locker-orange text-white font-bold hover:bg-locker-orange-hover shadow-lg shadow-locker-orange/20 transition-all active:scale-95"
                                                >
                                                    Confirmar
                                                </button>
                                            </div>
                                        </form>
                                    </div>

                                    {/* COLUMNA DERECHA: VISUALIZACIÓN DEL LOCKER */}
                                    <div className="w-full lg:w-1/2 flex justify-center perspective-1000">
                                        <motion.div 
                                            layoutId={`locker-visual-${selectedLocker.id}`}
                                            className="w-72 h-96 bg-locker-black-surface border-[6px] rounded-[3rem] flex flex-col items-center justify-center relative transition-all duration-500"
                                            style={{ 
                                                borderColor: assignForm.color,
                                                boxShadow: `0 0 80px ${assignForm.color}40, inset 0 0 20px ${assignForm.color}20`
                                            }}
                                        >
                                            {/* Efecto de luz superior */}
                                            <div 
                                                className="absolute top-0 w-1/2 h-1 rounded-full shadow-[0_0_20px_2px_currentColor]"
                                                style={{ color: assignForm.color, backgroundColor: assignForm.color }} 
                                            />

                                            <Box size={64} className="mb-4 text-white opacity-90" />
                                            <span className="text-6xl font-bold text-white tracking-tighter">{selectedLocker.code}</span>
                                            
                                            <div className="absolute bottom-8 px-4 py-1 rounded-full bg-black/50 backdrop-blur text-xs font-mono text-gray-400 border border-white/10">
                                                PREVIEW
                                            </div>
                                        </motion.div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            );
    }
  };

  if (loading) return <div className="h-screen bg-locker-black text-white flex items-center justify-center">Cargando...</div>;

  return (
    <div className="h-screen bg-locker-black text-white overflow-hidden flex flex-col relative">
      <div className="flex-1 overflow-y-auto p-6 pb-24">
        {renderContent()}
      </div>
      {/* BARRA INFERIOR (IGUAL QUE ANTES) */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-locker-black-surface/90 backdrop-blur-md border border-locker-black-border rounded-full px-6 py-3 flex items-center gap-8 shadow-2xl z-50">
          <NavButton icon={<Grid size={24} />} label="Lockers" active={currentView === 'grid'} onClick={() => setCurrentView('grid')} />
          <NavButton icon={<Key size={24} />} label="Mi Acceso" active={currentView === 'otp'} onClick={() => hasLocker && setCurrentView('otp')} disabled={!hasLocker} />
          <NavButton icon={<User size={24} />} label="Perfil" active={currentView === 'profile'} onClick={() => setCurrentView('profile')} />
          <div className="w-px h-8 bg-gray-700 mx-2"></div>
          <button onClick={handleLogout} className="p-2 rounded-full hover:bg-red-500/20 text-gray-400 hover:text-red-500 transition-colors"><LogOut size={20} /></button>
      </div>
    </div>
  );
};

// Componente NavButton igual...
const NavButton = ({ icon, label, active, onClick, disabled }) => (
    <div onClick={!disabled ? onClick : undefined} className={`flex flex-col items-center gap-1 group relative ${disabled ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'} ${active ? 'text-locker-orange' : 'text-gray-500'}`}>
        <motion.div whileHover={!disabled ? { y: -5 } : {}} className="p-2 rounded-xl group-hover:bg-white/5 transition-colors">{icon}</motion.div>
        <span className="pointer-events-none text-[10px] font-medium opacity-0 group-hover:opacity-100 transition-opacity absolute -top-8 bg-black px-2 py-1 rounded border border-gray-800 whitespace-nowrap z-50">{label}</span>
    </div>
);

export default Dashboard;