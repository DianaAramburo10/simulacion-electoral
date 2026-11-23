import math
import heapq
import json
import csv

from collections import deque, Counter
from datetime import datetime, timedelta
import mesa
from mesa.datacollection import DataCollector
import argparse
NUM_VERIFICADORES = 3
NUM_MAMPARAS = 3
INICIO = datetime(2024, 6, 2, 7, 30)
T_APERTURA = 30
T_CIERRE = 630
P_TROPIEZO = 0.005
P_CREDENCIAL = 0.025
P_FUNCIONARIO_FALTA = 0.1
P_ATAQUE = 0.05
P_TORNADO = 0.01
PACIENCIA_ESCALA = 50
K_PELEA = 0.03
K_REVOLTOSO = 0.04
UMBRAL_FILA_LARGA = 40
PARTIDOS = {'PTA': 'Partido del Taco', 'MT': 'Movimiento Tapatío', 'AJV': 'Alianza Jalisco Verde', 'FN': 'Frente Nopal'}
COALICION = ('PTA', 'FN')
ELECCIONES = ['Presidencia', 'Senaduría', 'Diputación federal', 'Gubernatura', 'Diputación local', 'Ayuntamiento']
PROPORCIONES = {'Presidencia': {'PTA': 0.38, 'MT': 0.22, 'AJV': 0.28, 'FN': 0.12}, 'Senaduría': {'PTA': 0.3, 'MT': 0.33, 'AJV': 0.25, 'FN': 0.12}, 'Diputación federal': {'PTA': 0.31, 'MT': 0.31, 'AJV': 0.26, 'FN': 0.12}, 'Gubernatura': {'PTA': 0.28, 'MT': 0.4, 'AJV': 0.18, 'FN': 0.14}, 'Diputación local': {'PTA': 0.29, 'MT': 0.37, 'AJV': 0.22, 'FN': 0.12}, 'Ayuntamiento': {'PTA': 0.27, 'MT': 0.41, 'AJV': 0.2, 'FN': 0.12}}
TIPOS_MARCA = {'normal': 0.935, 'dibujo_claro': 0.015, 'no_registrado': 0.005, 'blanco': 0.015, 'varias_marcas': 0.025, 'dibujo_ambiguo': 0.005}
GRUPOS_EDAD = {'18-29': (18, 29, 0.27, 0.52), '30-44': (30, 44, 0.3, 0.6), '45-64': (45, 64, 0.3, 0.7), '65+': (65, 90, 0.13, 0.62)}
PERFIL_HORARIO = {8: 9, 9: 13, 10: 15, 11: 14, 12: 11, 13: 8, 14: 7, 15: 7, 16: 8, 17: 8}

class Votante(mesa.Agent):

    def __init__(self, model, numero, edad, genero):
        super().__init__(model)
        self.id = numero
        self.nombre = f'Votante {numero}'
        self.edad = edad
        self.genero = genero
        self.estado = 'En camino'
        self.llegada = None
        self.salida = None
        self.t_fila = None
        self.espera = 0
        self.estres = 0
        self.paciencia = self.model.random.weibullvariate(PACIENCIA_ESCALA, 2)
        self.motivo_prioridad = None
        if edad >= 65:
            self.motivo_prioridad = 'adulto mayor'
        elif self.model.random.random() < 0.05:
            if genero == 'Mujer' and edad <= 44:
                self.motivo_prioridad = self.model.random.choice(['discapacidad', 'embarazo'])
            else:
                self.motivo_prioridad = 'discapacidad'
        self.prioritario = self.motivo_prioridad is not None
        self.revoltoso = self.model.random.random() < self.model.P_REVOLTOSO
        self.tramposo = self.model.random.random() < self.model.P_TRAMPOSO
        self.indeciso = self.model.random.random() < 0.1
        if self.revoltoso:
            self.estres = self.model.random.uniform(65, 90)
        else:
            self.estres = self.model.random.uniform(0, 30)
        self.umbral = self.estres + 0.5 * self.paciencia
        self.credencial_problema = None
        if self.model.random.random() < P_CREDENCIAL:
            self.credencial_problema = self.model.categorica({'casilla_equivocada': 0.6, 'vencida': 0.2, 'no_aparece': 0.2})
        self.personas_en_fila = 0
        self.mojandose = False
        self.pospuso = False
        self.ya_voto = False
        self.intento_doble = False
        self.boletas = None
        self.votos_emitidos = 0
        self.version = 0

    def percibir(self):
        self.personas_en_fila = len(self.model.fila_verificacion)
        self.mojandose = self.model.casilla.lloviendo and (not self.model.casilla.techo)

    def decidir_formarse(self):
        if self.intento_doble:
            return 'Formarse'
        if self.model.casilla.lloviendo and (not self.pospuso):
            r = self.model.random.random()
            if r < 0.35:
                return 'Posponer'
            if r < 0.45:
                return 'Desistir'
        if self.personas_en_fila > UMBRAL_FILA_LARGA and (not self.prioritario):
            if self.model.random.random() < 0.3:
                return 'Abandonar'
        return 'Formarse'

    def decidir_prioridad(self):
        return self.prioritario and self.personas_en_fila > 0 and (self.model.random.random() < 0.9)

    def actualizar_estres(self):
        self.estres += 0.5
        if self.mojandose:
            incremento = {'ligera': 1, 'moderada': 2, 'fuerte': 3}
            self.estres += incremento[self.model.casilla.intensidad]
        self.estres = min(100, self.estres)

    def decidir_en_fila(self):
        if self.estres >= self.umbral:
            return 'Abandonar'
        return 'Esperar'

    def marcar_boletas(self):
        boletas = {}
        for eleccion in ELECCIONES:
            partido = self.model.categorica(self.model.proporciones[eleccion])
            tipo = self.model.categorica(TIPOS_MARCA)
            if tipo == 'normal' and partido in COALICION and (self.model.random.random() < 0.1):
                tipo = 'ambos_coalicion'
            boletas[eleccion] = (partido, tipo)
        return boletas

    def decidir_votar_otra_vez(self):
        return self.tramposo and (not self.intento_doble)

    def recibir(self, performativa, contenido):
        if contenido == 'muestre su credencial':
            return 'inform', 'ya votó' if self.ya_voto else (self.credencial_problema or 'vigente')
        if contenido == 'muévanse bajo techo':
            self.estres = max(0, self.estres - 10)
            return 'agree', 'me muevo'
        if contenido == 'retírese de la fila':
            return 'agree', 'me retiro'
        return None

    def actuar(self, evento, t, recurso=-1):
        if evento == 'Llegada':
            self.model.llegada_votante(self, t)
        elif evento == 'Tick':
            self.percibir()
            if t >= T_APERTURA:
                self.actualizar_estres()
                if self.decidir_en_fila() == 'Abandonar':
                    self.model.abandonar_por_estres(self, t)
        elif evento == 'LlegaMampara':
            self.estado = 'Esperando mampara'
            self.model.fila_mampara.append(self)
            self.model.mampara(t)
        elif evento == 'Mampara':
            self.model.fin_mampara(self, recurso, t)
        elif evento == 'Urna':
            self.model.salir(self, t)

class Funcionario(mesa.Agent):

    def __init__(self, model, rol):
        super().__init__(model)
        self.rol = rol
        self.nombre = rol
        self.presente = True
        self.origen = 'propietario'

    def revisar_credencial(self, credencial):
        if credencial == 'ya votó':
            if self.model.random.random() < 0.99:
                return 'ya_voto'
            return 'ok_duplicado'
        if credencial != 'vigente':
            return credencial
        return 'ok'

    def actuar(self, votante, recurso, t):
        self.model.fin_verificacion(votante, recurso, t)

class Presidente(Funcionario):

    def decidir_mover_fila(self):
        return not self.model.casilla.techo and self.model.random.random() < 0.7

    def decidir_sacar_revoltoso(self):
        return self.model.random.random() < 0.15

    def decidir_voto_dudoso(self):
        if self.model.random.random() < 0.7:
            return 'nulo'
        return 'valido'

    def decidir_reubicar(self):
        return self.model.random.random() < 0.75

    def proteger_urna(self, atacantes):
        return self.model.random.random() < max(0.2, 0.9 - 0.04 * atacantes)

    def recibir(self, performativa, contenido):
        if contenido == 'pido pasar primero':
            return 'agree', 'pase primero'
        if contenido == 'pido recuento':
            return 'agree', 'se recuenta el voto'
        return None

class Representante(mesa.Agent):

    def __init__(self, model, partido):
        super().__init__(model)
        self.partido = partido
        self.nombre = f'Representante {partido}'
        self.combatividad = self.model.random.uniform(0.1, 0.5)

    def decidir_protestar(self):
        return self.model.random.random() < self.combatividad

class CAE(mesa.Agent):
    nombre = 'CAE'

    def recibir(self, performativa, contenido):
        if contenido == 'acta lista':
            return 'agree', 'llevo el acta al PREP'
        return None

    def transmitir(self, t):
        self.model.traslado = self.model.random.lognormvariate(math.log(20), 0.4)
        foto = self.model.random.uniform(2, 5)
        return t + self.model.traslado + foto

class Casilla:

    def __init__(self):
        self.instalada = False
        self.apertura = None
        self.pausada_hasta = 0
        self.suspendida_hasta = 0
        self.suspendida = False
        self.suspendida_definitiva = False
        self.cerrada = False
        self.fin_votacion = False
        self.robada = False
        self.lloviendo = False
        self.intensidad = None
        self.techo = False
        self.hubo_tornado = False
        self.ayudando_hasta = 0
        self.urna = {eleccion: [] for eleccion in ELECCIONES}
        self.inicio_escrutinio = None
        self.fin_escrutinio = None
        self.hora_prep = None
        self.estado_prep = 'Pendiente'
        self.resultados = {}
        self.incidentes = Counter()
        self.votos_perdidos = 0
        self.recuentos = 0
        self.max_fila = 0
        self.escrutadores_faltantes = 0

    def puede_atender(self, t):
        return self.instalada and (not self.suspendida) and (not self.suspendida_definitiva) and (not self.robada) and (not self.fin_votacion) and (t >= self.pausada_hasta)

class ModeloElectoral(mesa.Model):

    def __init__(self, modo='demo', seed=3, n_demo=80,
             lista_nominal=690, intervalo_llegadas=1.5,
             num_mamparas=NUM_MAMPARAS,
             eventos_externos=True):

        super().__init__(seed=seed)
        if modo not in ('demo', 'jornada'):
            raise ValueError('Modo inválido')
        self.MODO = modo
        self.SEMILLA = seed
        
        self.N_DEMO = n_demo
        self.LISTA_NOMINAL = lista_nominal
        self.INTERVALO_LLEGADAS = intervalo_llegadas
        self.NUM_MAMPARAS = num_mamparas
        self.EVENTOS_EXTERNOS = eventos_externos

        if self.N_DEMO < 1:
            raise ValueError("El número de votantes debe ser positivo")
        if self.INTERVALO_LLEGADAS <= 0:
            raise ValueError("El intervalo de llegadas debe ser positivo")
        if self.NUM_MAMPARAS < 1:
            raise ValueError("Debe existir al menos una mampara")

        self.t_min = 0.0
        self.P_REVOLTOSO = 0.12 if self.MODO == 'demo' else 0.03
        self.P_TRAMPOSO = 0.04 if self.MODO == 'demo' else 0.002
        if self.MODO == 'demo' and self.EVENTOS_EXTERNOS:
            self.FORZAR = {'lluvia': 75, 'ataque': 100, 'tornado': 130}
        else:
            self.FORZAR = {'lluvia': None, 'ataque': None, 'tornado': None}
        self.proporciones = {eleccion: self.dirichlet(PROPORCIONES[eleccion]) for eleccion in ELECCIONES}
        self.verificadores = [True] * NUM_VERIFICADORES
        self.mamparas = [True] * self.NUM_MAMPARAS
        self.fila_verificacion = deque()
        self.fila_mampara = deque()
        self.eventos = []
        self.eventos_unity = []
        self.mensajes = []
        self.contador = 0
        self.casilla = Casilla()
        self.presidente = Presidente(self, 'Presidente')
        self.personal_mesa = [self.presidente, Funcionario(self, 'Primer secretario'), Funcionario(self, 'Segundo secretario')]
        self.representantes = {partido: Representante(self, partido) for partido in PARTIDOS}
        self.cae = CAE(self)
        self.votantes = []
        if self.MODO == 'demo':
            tiempo_llegada = 10
            for i in range(self.N_DEMO):
                tiempo_llegada += self.random.expovariate(1 / self.INTERVALO_LLEGADAS)
                votante = self.crear_votante(i + 1)
                self.votantes.append(votante)
                self.nuevo_evento(tiempo_llegada, 'Llegada', votante)
        else:
            numero = 0
            for grupo, datos in GRUPOS_EDAD.items():
                edad_minima, edad_maxima, fraccion, participacion = datos
                cantidad = round(self.LISTA_NOMINAL * fraccion)
                for _ in range(cantidad):
                    if self.random.random() >= participacion:
                        continue
                    numero += 1
                    genero = 'Mujer' if self.random.random() < 0.52 else 'Hombre'
                    votante = Votante(self, numero, self.random.randint(edad_minima, edad_maxima), genero)
                    self.votantes.append(votante)
                    if self.random.random() < 0.05:
                        llegada = self.random.uniform(0, 30)
                    else:
                        h = self.categorica({hora: porcentaje / 100 for hora, porcentaje in PERFIL_HORARIO.items()})
                        llegada = (h - 7.5) * 60 + self.random.uniform(0, 60)
                    self.nuevo_evento(llegada, 'Llegada', votante)
        self.nuevo_evento(0, 'Instalacion')
        self.nuevo_evento(0, 'Tick')
        self.nuevo_evento(T_CIERRE, 'Cierre')


        if self.EVENTOS_EXTERNOS:
            for i in range(10):
                self.nuevo_evento(T_APERTURA + 60 * i, 'Clima')

            if self.FORZAR['lluvia'] is not None:
                self.nuevo_evento(
                    self.FORZAR['lluvia'], 'Clima', None, 'forzada'
                )

            if self.FORZAR['ataque'] is not None:
                self.nuevo_evento(self.FORZAR['ataque'], 'Ataque')
            elif self.random.random() < P_ATAQUE:
                self.nuevo_evento(
                    self.random.uniform(90, 570), 'Ataque'
                )

            if self.FORZAR['tornado'] is not None:
                self.nuevo_evento(self.FORZAR['tornado'], 'Tornado')
            elif self.random.random() < P_TORNADO:
                self.nuevo_evento(
                    self.random.uniform(120, 560), 'Tornado'
                )
        
        self.datacollector = DataCollector(model_reporters={'Tiempo_min': 't_min', 'Fila_verificacion': lambda m: len(m.fila_verificacion), 'Fila_mampara': lambda m: len(m.fila_mampara), 'Fila_maxima': lambda m: m.casilla.max_fila, 'Votantes_atendidos': lambda m: sum((v.ya_voto for v in m.votantes)), 'Espera_promedio': lambda m: m.metricas()['espera_promedio']})
        self.datacollector.collect(self)

    def hora(self, t):
        if t is None:
            return '--:--'
        return (INICIO + timedelta(minutes=t)).strftime('%H:%M')

    def categorica(self, probabilidades):
        r = self.random.random()
        acumulado = 0
        for opcion, probabilidad in probabilidades.items():
            acumulado += probabilidad
            if r < acumulado:
                return opcion
        return list(probabilidades)[-1]

    def dirichlet(self, proporciones, concentracion=300):
        valores = {}
        for partido, probabilidad in proporciones.items():
            valores[partido] = self.random.gammavariate(concentracion * probabilidad, 1)
        total = sum(valores.values())
        return {partido: valor / total for partido, valor in valores.items()}

    def poisson(self, media):
        limite = math.exp(-media)
        producto = 1
        k = 0
        while producto > limite:
            producto *= self.random.random()
            k += 1
        return k - 1

    def triangular(self, minimo, moda, maximo):
        return self.random.triangular(minimo, maximo, moda)

    def normal_truncada(self, media, desviacion, minimo):
        while True:
            valor = self.random.gauss(media, desviacion)
            if valor >= minimo:
                return valor

    def nuevo_evento(self, tiempo, tipo, votante=None, recurso=-1):
        self.contador += 1
        heapq.heappush(self.eventos, (tiempo, self.contador, tipo, votante, recurso))

    
    def enviar_a_unity(self, t, tipo, texto, votante=None, importante=True, recurso=None, **extra):
        # recurso: índice del verificador o mampara; la última mampara es la accesible
        evento = {
            't_min': round(t, 2),
            'hora': self.hora(t),
            'tipo': tipo,
            'votante': votante.id if votante else None,
            'estado': votante.estado if votante else None,
            'edad': votante.edad if votante else None,
            'genero': votante.genero if votante else None,
            'prioritario': votante.prioritario if votante else None,
            'motivo_prioridad': votante.motivo_prioridad if votante else None,
            'recurso': recurso,
            'texto': texto
        }
        evento.update(extra)

        self.eventos_unity.append(evento)

        if importante or self.MODO == 'demo':
            print(f'{self.hora(t)} | {texto}')


    def enviar(self, t, emisor, receptor, performativa, contenido):
        # mensaje tipo FIPA; el receptor decide la respuesta en su método recibir
        self.mensajes.append((round(t, 2), self.hora(t), emisor.nombre, receptor.nombre, performativa, contenido))
        respuesta = receptor.recibir(performativa, contenido)
        if respuesta is None:
            return None
        self.mensajes.append((round(t, 2), self.hora(t), receptor.nombre, emisor.nombre, *respuesta))
        return respuesta[1]

    def tiempo_disponible(self, t):
        return max(t, self.casilla.pausada_hasta, self.casilla.suspendida_hasta)

    def pausar(self, t, minutos):
        self.casilla.pausada_hasta = max(self.casilla.pausada_hasta, t + minutos)
        self.nuevo_evento(self.casilla.pausada_hasta, 'Reanudar')

    def suspender(self, t, minutos, motivo):
        self.casilla.suspendida = True
        self.casilla.suspendida_hasta = max(self.casilla.suspendida_hasta, t + minutos)
        self.nuevo_evento(self.casilla.suspendida_hasta, 'FinSuspension', None, motivo)

    def reanudar(self, t):
        if self.casilla.robada or self.casilla.suspendida_definitiva:
            return
        if t < self.tiempo_disponible(0):
            return
        self.casilla.suspendida = False
        self.verificar(t)
        self.mampara(t)

    def instalacion(self, t):
        suplentes = sum((self.random.random() < 0.9 for _ in range(3)))
        faltantes = 0
        roles = self.personal_mesa + [Funcionario(self, f'Escrutador {i}') for i in range(1, 4)]
        for funcionario in roles:
            if self.random.random() < P_FUNCIONARIO_FALTA:
                faltantes += 1
                self.casilla.incidentes['Funcionario no llegó'] += 1
                if suplentes > 0:
                    suplentes -= 1
                    funcionario.origen = 'suplente'
                    self.enviar_a_unity(t, 'Funcionario ausente', f'Falta {funcionario.rol}. Lo sustituye un suplente.')
                else:
                    funcionario.presente = False
                    funcionario.origen = 'vacante'
                    self.enviar_a_unity(t, 'Funcionario ausente', f'Falta {funcionario.rol} y no hay suplente.')
        self.casilla.escrutadores_faltantes = sum((not funcionario.presente for funcionario in roles[3:]))
        duracion = self.triangular(25, 40, 90)
        duracion += sum((self.random.uniform(5, 15) for _ in range(faltantes)))
        self.casilla.apertura = max(T_APERTURA, duracion)
        self.enviar_a_unity(t, 'Instalación', 'Comienza la instalación de la casilla.')
        self.nuevo_evento(self.casilla.apertura, 'Apertura')

    def apertura(self, t):
        for funcionario in self.personal_mesa:
            if funcionario.presente:
                continue
            candidatos = [v for v in self.fila_verificacion if not v.credencial_problema and (not v.tramposo) and (not v.revoltoso)]
            if not candidatos:
                continue
            votante = candidatos[0]
            self.fila_verificacion.remove(votante)
            funcionario.presente = True
            funcionario.origen = 'ciudadano de la fila'
            votante.estado = 'Funcionario (tomado de la fila)'
            votante.espera += max(0, t - votante.t_fila)
            votante.boletas = votante.marcar_boletas()
            self.depositar(votante, t)
            self.enviar_a_unity(t, 'Toma de fila', f'El presidente toma al votante {votante.id} de la fila como {funcionario.rol}.', votante)
        self.casilla.instalada = True
        activos = sum((f.presente for f in self.personal_mesa))
        self.enviar_a_unity(t, 'Apertura', f'La casilla electoral abre sus puertas con {activos} verificadores y {len(self.fila_verificacion)} personas formadas.')
        self.verificar(t)

    def llegada_votante(self, votante, t):
        if votante.ya_voto and (not votante.intento_doble):
            return
        if self.casilla.robada or self.casilla.suspendida_definitiva:
            votante.estado = 'Sin casilla'
            votante.salida = t
            self.enviar_a_unity(t, 'Sin casilla', f'Votante {votante.id} llega y ya no hay casilla.', votante, importante=False)
            return
        if t >= T_CIERRE or self.casilla.cerrada:
            votante.estado = 'Llegó después del cierre'
            votante.salida = t
            self.enviar_a_unity(t, 'Llegada tardía', f'Votante {votante.id} llega después del cierre.', votante, importante=False)
            return
        if votante.llegada is None:
            votante.llegada = t
        votante.percibir()
        decision = votante.decidir_formarse()
        if decision == 'Posponer':
            votante.pospuso = True
            votante.estado = 'Pospuso llegada'
            self.nuevo_evento(t + self.random.expovariate(1 / 60), 'Llegada', votante)
            return
        if decision == 'Desistir':
            votante.estado = 'Desistió (lluvia)'
            votante.salida = t
            self.enviar_a_unity(t, 'Desiste', f'Votante {votante.id} se regresa a su casa por la lluvia.', votante)
            return
        if decision == 'Abandonar':
            votante.estado = 'No se formó (fila larga)'
            votante.salida = t
            self.enviar_a_unity(t, 'Abandono', f'Votante {votante.id} ve {votante.personas_en_fila} personas y decide no formarse.', votante)
            return
        self.formar(votante, t)
        self.verificar(t)

    def formar(self, votante, t):
        votante.estado = 'Esperando verificación'
        votante.t_fila = t
        votante.percibir()
        posicion = 0
        for i, otro in enumerate(self.fila_verificacion):
            if otro.prioritario:
                posicion = i + 1
        if votante.decidir_prioridad() and posicion < len(self.fila_verificacion) and self.enviar(t, votante, self.presidente, 'request', 'pido pasar primero') == 'pase primero':
            self.fila_verificacion.insert(posicion, votante)
            self.enviar_a_unity(t, 'Prioridad', f'Votante {votante.id} ({votante.edad} años, {votante.motivo_prioridad}) pide pasar primero y se adelanta {votante.personas_en_fila - posicion} lugares.', votante)
        else:
            self.fila_verificacion.append(votante)
            self.enviar_a_unity(t, 'Formarse', f'Votante {votante.id} se forma.', votante, importante=False)
        self.casilla.max_fila = max(self.casilla.max_fila, len(self.fila_verificacion))

    def verificar(self, t):
        if not self.casilla.puede_atender(t):
            return
        for i in range(NUM_VERIFICADORES):
            if not self.fila_verificacion:
                break
            if not self.verificadores[i]:
                continue
            if not self.personal_mesa[i].presente:
                continue
            votante = self.fila_verificacion.popleft()
            self.verificadores[i] = False
            votante.estado = 'Verificando'
            votante.espera += max(0, t - votante.t_fila)
            duracion = self.random.lognormvariate(math.log(50), 0.4) / 60
            if votante.edad >= 65:
                duracion *= 1.3
            if t < self.casilla.ayudando_hasta:
                duracion *= 1.25
            if self.personal_mesa[i].origen == 'ciudadano de la fila':
                duracion *= 1.1
            if votante.credencial_problema or votante.ya_voto:
                duracion += self.random.uniform(1, 3)
            self.nuevo_evento(t + duracion, 'Verificar', votante, i)
            self.enviar_a_unity(t, 'Verificación', f'Votante {votante.id} inicia verificación.', votante, importante=False, recurso=i)

    def fin_verificacion(self, votante, recurso, t):
        self.verificadores[recurso] = True
        funcionario = self.personal_mesa[recurso]
        credencial = self.enviar(t, funcionario, votante, 'request', 'muestre su credencial')
        resultado = funcionario.revisar_credencial(credencial)
        if resultado in ('ok', 'ok_duplicado'):
            self.enviar(t, funcionario, votante, 'agree', 'pase a la mampara')
        else:
            self.enviar(t, funcionario, votante, 'refuse', resultado)
        if resultado == 'ya_voto':
            votante.estado = 'Rechazado (doble voto)'
            votante.salida = t
            self.casilla.incidentes['Intento de doble voto'] += 1
            self.enviar_a_unity(t, 'Doble voto', f'Votante {votante.id} intenta votar otra vez y es rechazado.', votante)
        elif resultado in ('vencida', 'no_aparece', 'casilla_equivocada'):
            textos = {'vencida': 'Rechazado (credencial vencida)', 'no_aparece': 'Rechazado (no aparece en lista)', 'casilla_equivocada': 'Enviado a la casilla contigua'}
            votante.estado = textos[resultado]
            votante.salida = t
            self.casilla.incidentes['Problema de credencial'] += 1
            self.enviar_a_unity(t, 'Credencial', f'Votante {votante.id}: {votante.estado}', votante)
        else:
            if resultado == 'ok_duplicado':
                self.casilla.incidentes['Doble voto no detectado'] += 1
            votante.estado = 'Caminando a mampara'
            self.nuevo_evento(t + self.traslado(votante, t), 'LlegaMampara', votante)
        self.verificar(t)

    def traslado(self, votante, t):
        duracion = self.random.uniform(0.1, 0.3)
        if self.random.random() < P_TROPIEZO:
            self.casilla.incidentes['Tropiezo'] += 1
            if self.random.random() < 0.15:
                demora = self.random.uniform(3, 8)
                self.casilla.ayudando_hasta = max(self.casilla.ayudando_hasta, t + demora)
                texto = f'Votante {votante.id} se cae. Un escrutador lo ayuda.'
            else:
                demora = self.random.uniform(0.5, 1)
                texto = f'Votante {votante.id} tropieza pero puede continuar.'
            duracion += demora
            self.enviar_a_unity(t, 'Tropiezo', texto, votante)
        return duracion

    def mampara(self, t):
        if not self.casilla.puede_atender(t):
            return
        accesible = self.NUM_MAMPARAS - 1
        for i in range(self.NUM_MAMPARAS):
            if not self.mamparas[i] or not self.fila_mampara:
                continue
            if i == accesible:
                # preferencia para discapacidad, pero la puede usar cualquiera
                votante = next((v for v in self.fila_mampara if v.motivo_prioridad == 'discapacidad'), self.fila_mampara[0])
            else:
                # la silla de ruedas solo cabe en la accesible
                votante = next((v for v in self.fila_mampara if v.motivo_prioridad != 'discapacidad'), None)
                if votante is None:
                    continue
            self.fila_mampara.remove(votante)
            self.mamparas[i] = False
            votante.estado = 'En mampara'
            duracion = self.random.gammavariate(4, 40) / 60
            if votante.prioritario:
                duracion *= 1.5
            if votante.indeciso:
                duracion *= 1.5
            self.nuevo_evento(t + duracion, 'Mampara', votante, i)
            self.enviar_a_unity(t, 'Mampara', f'Votante {votante.id} comienza a votar.', votante, importante=False, recurso=i)

    def depositar(self, votante, t):
        for eleccion, marca in votante.boletas.items():
            self.casilla.urna[eleccion].append(marca)
        votante.ya_voto = True
        votante.votos_emitidos += 1
        votante.salida = t

    def salir(self, votante, t):
        if self.casilla.robada:
            votante.estado = 'Interrumpido por robo'
            votante.salida = t
            return
        primera_vez = not votante.ya_voto
        self.depositar(votante, t)
        if primera_vez:
            votante.estado = 'Finalizado'
        else:
            votante.estado = 'Votó dos veces'
        self.enviar_a_unity(t, 'Salida', f'Votante {votante.id} deposita sus boletas y sale.', votante, importante=False)
        if votante.decidir_votar_otra_vez():
            votante.intento_doble = True
            regreso = t + self.random.uniform(10, 60)
            if regreso < T_CIERRE:
                self.nuevo_evento(regreso, 'Llegada', votante)

    def tick(self, t):
        if not self.casilla.fin_votacion and (not self.casilla.robada):
            for votante in list(self.fila_verificacion):
                votante.actuar('Tick', t)
            self.revisar_peleas(t)
        if t >= T_CIERRE:
            self.revisar_fin_votacion(t)
        if not self.casilla.fin_votacion and (not self.casilla.robada) and (not self.casilla.suspendida_definitiva) and (t < 1350):
            self.nuevo_evento(t + 1, 'Tick')

    def revisar_peleas(self, t):
        if not self.casilla.instalada:
            return
        if t < self.casilla.pausada_hasta:
            return
        fila = list(self.fila_verificacion)
        for i in range(len(fila) - 1):
            a = fila[i]
            b = fila[i + 1]
            probabilidad = 0
            if a.estres > 70 and b.estres > 70:
                probabilidad = K_PELEA * a.estres * b.estres / 10000
            elif a.revoltoso and a.estres > 70 or (b.revoltoso and b.estres > 70):
                probabilidad = K_REVOLTOSO
            if self.random.random() >= probabilidad:
                continue
            self.casilla.incidentes['Pelea'] += 1
            duracion = self.random.uniform(2, 5)
            self.pausar(t, duracion)
            for vecino in fila[max(0, i - 3):i + 5]:
                vecino.estres = min(100, vecino.estres + 10)
            self.enviar_a_unity(t, 'Pelea', f'Votantes {a.id} y {b.id} comienzan una pelea.')
            if self.presidente.decidir_sacar_revoltoso():
                involucrados = [v for v in (a, b) if v.revoltoso]
                if not involucrados:
                    involucrados = [a, b]
                for votante in involucrados:
                    if votante in self.fila_verificacion:
                        self.enviar(t, self.presidente, votante, 'request', 'retírese de la fila')
                        self.fila_verificacion.remove(votante)
                        votante.estado = 'Retirado por pelea'
                        votante.salida = t
                        self.enviar_a_unity(t, 'Seguridad', f'Votante {votante.id} es retirado de la fila.', votante)
            break

    def revisar_clima(self, t, forzada=False):
        if self.casilla.lloviendo or self.casilla.fin_votacion:
            return
        h = int(7.5 + t / 60)
        probabilidad = 0.05 if h < 15 else 0.3
        if not forzada and self.random.random() >= probabilidad:
            return
        self.casilla.lloviendo = True
        if forzada:
            self.casilla.intensidad = 'moderada'
            duracion = self.random.uniform(40, 70)
        else:
            self.casilla.intensidad = self.categorica({'ligera': 0.5, 'moderada': 0.35, 'fuerte': 0.15})
            duracion = self.random.expovariate(1 / 45)
        self.enviar_a_unity(t, 'Lluvia', f'Comienza lluvia {self.casilla.intensidad}.')
        self.nuevo_evento(t + duracion, 'FinLluvia')
        if self.presidente.decidir_mover_fila():
            mover = self.random.uniform(3, 6)
            self.pausar(t, mover)
            self.nuevo_evento(t + mover, 'TechoListo')
            self.enviar_a_unity(t, 'Mover fila', 'El presidente decide mover la fila bajo techo.')
        if self.casilla.intensidad == 'fuerte' and duracion > 60:
            self.nuevo_evento(t + 60, 'Inundacion')

    def inundacion(self, t):
        if not self.casilla.lloviendo or self.casilla.robada or self.casilla.fin_votacion:
            return
        self.casilla.incidentes['Inundación'] += 1
        duracion = self.triangular(20, 40, 90)
        for votante in list(self.fila_verificacion):
            if self.random.random() < 0.3:
                self.fila_verificacion.remove(votante)
                votante.estado = 'Abandonó por inundación'
                votante.salida = t
                self.enviar_a_unity(t, 'Abandono', f'Votante {votante.id} abandona la fila por la inundación.', votante, importante=False)
        self.suspender(t, duracion, 'inundación')
        self.enviar_a_unity(t, 'Inundación', f'Se suspende la casilla {duracion:.1f} minutos.')

    def ataque(self, t):
        if (
            self.casilla.fin_votacion
            or self.casilla.robada
            or self.casilla.suspendida_definitiva
            or self.casilla.suspendida
        ):
            return
        atacantes = max(3, self.poisson(8))
        self.casilla.incidentes['Ataque Minion'] += 1
        self.enviar_a_unity(t, 'Ataque', f'¡Llegan {atacantes} Minions para robarse la casilla!', atacantes=atacantes)
        for votante in list(self.fila_verificacion):
            votante.estres = 100
            if self.random.random() < 0.8:
                self.fila_verificacion.remove(votante)
                votante.estado = 'Huyó de los Minions'
                votante.salida = t
                self.enviar_a_unity(t, 'Huida', f'Votante {votante.id} huye de los Minions.', votante, importante=False)
        if self.presidente.proteger_urna(atacantes):
            self.casilla.incidentes['Urna protegida'] += 1
            duracion = self.triangular(10, 30, 120)
            self.enviar_a_unity(t, 'Urna protegida', f'Los funcionarios protegen la urna y los Minions huyen. Votación suspendida {duracion:.0f} min.')
            self.suspender(t, duracion, 'ataque Minion')
            return
        probabilidad_exito = min(0.85, 0.35 + 0.04 * atacantes)
        if self.random.random() < probabilidad_exito:
            self.casilla.robada = True
            self.casilla.fin_votacion = True
            self.casilla.suspendida_definitiva = True
            self.casilla.cerrada = True
            self.casilla.incidentes['Robo exitoso'] += 1
            self.casilla.votos_perdidos += len(self.casilla.urna['Presidencia'])
            self.casilla.urna = {eleccion: [] for eleccion in ELECCIONES}
            self.casilla.estado_prep = 'Sin acta (material robado)'
            for votante in list(self.fila_verificacion) + list(self.fila_mampara):
                votante.estado = 'Sin casilla'
                votante.salida = t
                self.enviar_a_unity(t, 'Sin casilla', f'Votante {votante.id} se queda sin casilla y se retira.', votante, importante=False)
            self.fila_verificacion.clear()
            self.fila_mampara.clear()
            self.enviar_a_unity(t, 'Robo exitoso', '¡LOS MINIONS SE LLEVAN LA CASILLA! La votación queda suspendida definitivamente.')
        else:
            self.casilla.incidentes['Robo fallido'] += 1
            fallas = ['Se les cae la urna antes de escapar.', 'Su vehículo no arranca.', 'Chocan entre ellos.', 'Se llevan una caja vacía por error.', 'Se rompe su carrito de transporte.']
            falla = self.random.choice(fallas)
            duracion = self.triangular(10, 20, 40)
            self.enviar_a_unity(t, 'Robo fallido', f'¡PLAN FALLIDO! {falla} Los Minions huyen sin los votos.')
            self.suspender(t, duracion, 'ataque Minion fallido')
            self.enviar_a_unity(t, 'Suspensión', f'La casilla se reorganiza durante {duracion:.1f} minutos.')

    
    def tornado(self, t):
        if (
            self.casilla.hubo_tornado
            or self.casilla.fin_votacion
            or self.casilla.robada
        ):
            return

        self.casilla.hubo_tornado = True
        self.casilla.incidentes['Tornado'] += 1

        evacuacion = self.triangular(10, 30, 120)

        self.enviar_a_unity(
            t,
            'Tornado',
            '¡TORNADO! Se evacúa la casilla.'
        )

        # Identificar a los votantes en filas
        afectados = {}

        for votante in list(self.fila_verificacion) + list(self.fila_mampara):
            afectados[votante.id] = votante

        # Identificar también a quienes están siendo atendidos
        eventos_atencion = {'Verificar', 'LlegaMampara', 'Mampara', 'Urna'}

        for evento in self.eventos:
            tiempo, numero, tipo, votante, recurso = evento

            if tipo in eventos_atencion and votante is not None:
                afectados[votante.id] = votante

        # Cancelar los eventos de atención de los evacuados
        self.eventos = [
            evento
            for evento in self.eventos
            if not (
                evento[2] in eventos_atencion
                and evento[3] is not None
                and evento[3].id in afectados
            )
        ]

        # Reconstruir la cola de prioridad de heapq
        heapq.heapify(self.eventos)

        # Vaciar filas y liberar verificadores y mamparas
        self.fila_verificacion.clear()
        self.fila_mampara.clear()

        self.verificadores = [True] * NUM_VERIFICADORES
        self.mamparas = [True] * self.NUM_MAMPARAS

        # Decidir qué ocurre con cada votante evacuado
        for votante in afectados.values():
            estado_anterior = votante.estado

            if (
                votante.t_fila is not None
                and estado_anterior == 'Esperando verificación'
            ):
                votante.espera += max(0, t - votante.t_fila)

            votante.t_fila = None

            if self.random.random() < 0.4:
                votante.estado = 'Evacuado (regresará)'

                regreso = (
                    t
                    + evacuacion
                    + self.random.uniform(0, 20)
                )

                self.nuevo_evento(regreso, 'Llegada', votante)

                self.enviar_a_unity(
                    t,
                    'Evacuación',
                    f'Votante {votante.id} evacúa y planea regresar.',
                    votante,
                    importante=False
                )

            else:
                votante.estado = 'Evacuado (no regresó)'
                votante.salida = t

                self.enviar_a_unity(
                    t,
                    'Evacuación',
                    f'Votante {votante.id} evacúa y no regresará.',
                    votante,
                    importante=False
                )

        # Posible pérdida de votos ya depositados
        if self.random.random() < 0.3:
            perdidos = int(
                len(self.casilla.urna['Presidencia'])
                * self.random.uniform(0.3, 1)
            )

            for eleccion in ELECCIONES:
                self.random.shuffle(self.casilla.urna[eleccion])
                self.casilla.urna[eleccion] = (
                    self.casilla.urna[eleccion][perdidos:]
                )

            self.casilla.votos_perdidos += perdidos

            self.enviar_a_unity(
                t,
                'Material perdido',
                f'El tornado provoca la pérdida de {perdidos} votos.'
            )

        # Decidir si la casilla puede reubicarse
        if self.presidente.decidir_reubicar():
            self.casilla.techo = True

            self.suspender(t, evacuacion, 'tornado')

            self.enviar_a_unity(
                t,
                'Reubicación',
                'El presidente decide reubicar la casilla dentro del plantel.'
            )

        else:
            self.casilla.suspendida_definitiva = True
            self.casilla.cerrada = True

            self.enviar_a_unity(
                t,
                'Suspensión definitiva',
                'La casilla no puede continuar después del tornado.'
            )


    def cierre(self, t):
        self.casilla.cerrada = True
        self.enviar_a_unity(t, 'Cierre', 'Son las 18:00. Se cierra la casilla para nuevas llegadas.')
        self.revisar_fin_votacion(t)

    def revisar_fin_votacion(self, t):
        if (
            self.casilla.fin_votacion
            or self.casilla.robada
            
            or self.casilla.suspendida
            or self.casilla.suspendida_definitiva
        ):
            return

        if not self.casilla.cerrada:
            return

        if self.fila_verificacion or self.fila_mampara:
            return

        if not all(self.verificadores):
            return

        if not all(self.mamparas):
            return

        pendientes = {"Verificar", "LlegaMampara", "Mampara", "Urna"}

        if any(evento[2] in pendientes for evento in self.eventos):
            return

        self.escrutinio(t)

    def escrutinio(self, t):
        if self.casilla.fin_votacion:
            return
        self.casilla.fin_votacion = True
        self.casilla.inicio_escrutinio = t
        self.enviar_a_unity(t, 'Escrutinio', 'Comienza el conteo de votos.')
        lentitud = 1 + 0.3 * self.casilla.escrutadores_faltantes
        tiempo_total = 0
        for eleccion in ELECCIONES:
            conteo = Counter()
            tiempo = self.normal_truncada(10, 3, 3)
            for partido, tipo in self.casilla.urna[eleccion]:
                tiempo += self.triangular(2, 4, 10) / 60 * lentitud
                if tipo in ('normal', 'dibujo_claro'):
                    conteo[partido] += 1
                elif tipo == 'ambos_coalicion':
                    conteo['PTA+FN'] += 1
                elif tipo == 'no_registrado':
                    conteo['No registrado'] += 1
                elif tipo == 'dibujo_ambiguo':
                    tiempo += self.random.uniform(0.5, 1.5)
                    decision = self.presidente.decidir_voto_dudoso()
                    if decision == 'nulo':
                        conteo['Nulos'] += 1
                        representante = self.representantes[partido]
                        if representante.decidir_protestar() and self.enviar(t + tiempo_total + tiempo, representante, self.presidente, 'request', 'pido recuento') == 'se recuenta el voto':
                            recuento = self.random.uniform(5, 15)
                            tiempo += recuento
                            self.casilla.recuentos += 1
                    else:
                        conteo[partido] += 1
                else:
                    conteo['Nulos'] += 1
            tiempo += self.normal_truncada(15, 5, 5)
            self.casilla.resultados[eleccion] = conteo
            tiempo_total += tiempo
        self.nuevo_evento(t + tiempo_total, 'FinEscrutinio')

    def fin_escrutinio(self, t):
        self.casilla.fin_escrutinio = t
        self.enviar_a_unity(t, 'Fin escrutinio', 'Termina el conteo de votos.')
        self.enviar(t, self.presidente, self.cae, 'inform', 'acta lista')
        self.nuevo_evento(self.cae.transmitir(t), 'PREP')

    def prep(self, t):
        self.casilla.hora_prep = t
        self.casilla.estado_prep = 'Transmitida'
        self.enviar_a_unity(t, 'PREP', 'El CAE transmite el acta al PREP.')

    def crear_votante(self, numero):
        grupo = self.categorica({nombre: datos[2] for nombre, datos in GRUPOS_EDAD.items()})
        edad_minima, edad_maxima = GRUPOS_EDAD[grupo][:2]
        genero = 'Mujer' if self.random.random() < 0.52 else 'Hombre'
        return Votante(self, numero, self.random.randint(edad_minima, edad_maxima), genero)

    def abandonar_por_estres(self, votante, t):
        self.fila_verificacion.remove(votante)
        votante.estado = 'Abandonó por estrés'
        votante.salida = t
        votante.espera += max(0, t - votante.t_fila)
        self.enviar_a_unity(t, 'Abandono', f'Votante {votante.id} abandona por estrés.', votante)

    def fin_mampara(self, votante, recurso, t):
        self.mamparas[recurso] = True
        votante.boletas = votante.marcar_boletas()
        votante.estado = 'Caminando a urna'
        duracion = self.triangular(15, 30, 60) / 60
        self.nuevo_evento(t + self.traslado(votante, t) + duracion, 'Urna', votante)
        self.mampara(t)
        self.verificar(t)

    def _procesar_evento(self):
        t, _, tipo, votante, recurso = heapq.heappop(self.eventos)
        self.t_min = t
        eventos_atencion = {'Verificar', 'LlegaMampara', 'Mampara', 'Urna'}
        if tipo in eventos_atencion:
            if self.casilla.robada or self.casilla.suspendida_definitiva:
                if votante is not None:
                    votante.estado = 'Proceso interrumpido'
                    votante.salida = t
                    self.enviar_a_unity(t, 'Proceso interrumpido', f'Votante {votante.id} no pudo terminar de votar.', votante, importante=False)
                if tipo == 'Verificar':
                    self.verificadores[recurso] = True
                elif tipo == 'Mampara':
                    self.mamparas[recurso] = True
                self.revisar_fin_votacion(t)
                return
            disponible = max(t, self.casilla.suspendida_hasta)
            if t < disponible:
                self.nuevo_evento(disponible, tipo, votante, recurso)
                return
        if tipo == 'Llegada':
            votante.actuar(tipo, t, recurso)
        elif tipo == 'Verificar':
            self.personal_mesa[recurso].actuar(votante, recurso, t)
        elif tipo == 'LlegaMampara':
            votante.actuar(tipo, t, recurso)
        elif tipo == 'Mampara':
            votante.actuar(tipo, t, recurso)
        elif tipo == 'Urna':
            votante.actuar(tipo, t, recurso)
        elif tipo == 'Instalacion':
            self.instalacion(t)
        elif tipo == 'Apertura':
            self.apertura(t)
        elif tipo == 'Tick':
            self.tick(t)
        elif tipo == 'Reanudar':
            self.reanudar(t)
        elif tipo == 'FinSuspension':
            if t >= self.casilla.suspendida_hasta:
                self.casilla.suspendida = False
                if not (self.casilla.robada or self.casilla.suspendida_definitiva):
                    self.enviar_a_unity(t, 'Reanudación', f'Se reanuda después de: {recurso}')
                    self.reanudar(t)
        elif tipo == 'Clima':
            self.revisar_clima(t, forzada=recurso == 'forzada')
        elif tipo == 'TechoListo':
            self.casilla.techo = True
            for votante in self.fila_verificacion:
                self.enviar(t, self.presidente, votante, 'request', 'muévanse bajo techo')
        elif tipo == 'FinLluvia':
            self.casilla.lloviendo = False
            self.enviar_a_unity(t, 'Fin lluvia', 'Deja de llover.')
        elif tipo == 'Inundacion':
            self.inundacion(t)
        elif tipo == 'Ataque':
            self.ataque(t)
        elif tipo == 'Tornado':
            self.tornado(t)
        elif tipo == 'Cierre':
            self.cierre(t)
        elif tipo == 'FinEscrutinio':
            self.fin_escrutinio(t)
        elif tipo == 'PREP':
            self.prep(t)
        if t >= T_CIERRE or self.casilla.suspendida_definitiva:
            self.revisar_fin_votacion(t)

    def step(self):
        if not self.eventos:
            self.running = False
            return
        self._procesar_evento()
        self.datacollector.collect(self)
        self.running = bool(self.eventos)

    def metricas(self):
        votaron = [v for v in self.votantes if v.ya_voto]
        return {'votantes_atendidos': len(votaron), 'fila_maxima': self.casilla.max_fila, 'espera_promedio': sum((v.espera for v in votaron)) / len(votaron) if votaron else 0.0}


    def exportar_resultados_graficas(self):
        # Guardar los resultados de las seis elecciones
        with open(
            "resultados_elecciones.csv",
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["Eleccion", "Partido", "Votos"])

            for eleccion, conteo in self.casilla.resultados.items():
                for partido, nombre in PARTIDOS.items():
                    escritor.writerow([
                        eleccion,
                        nombre,
                        conteo[partido]
                    ])

                escritor.writerow([
                    eleccion,
                    "Coalición doble marca PTA+FN",
                    conteo["PTA+FN"]
                ])

                escritor.writerow([
                    eleccion,
                    "Votos nulos",
                    conteo["Nulos"]
                ])

                escritor.writerow([
                    eleccion,
                    "No registrados",
                    conteo["No registrado"]
                ])

        # Guardar edad, género y participación
        with open(
            "demografia_votantes.csv",
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow([
                "Grupo_edad", "Genero", "Voto"
            ])

            for votante in self.votantes:
                if votante.edad <= 29:
                    grupo = "18-29"
                elif votante.edad <= 44:
                    grupo = "30-44"
                elif votante.edad <= 64:
                    grupo = "45-64"
                else:
                    grupo = "65+"

                escritor.writerow([
                    grupo,
                    votante.genero,
                    "Si" if votante.ya_voto else "No"
                ])

        with open("mensajes_agentes.csv", "w", newline="", encoding="utf-8-sig") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["t_min", "Hora", "Emisor", "Receptor", "Performativa", "Contenido"])
            escritor.writerows(self.mensajes)

        print("Archivos para gráficas exportados correctamente.")



    def resultados_finales(self):
        print('\n' + '=' * 70)
        print('RESULTADOS DE LA SIMULACIÓN')
        print('=' * 70)
        votaron = [v for v in self.votantes if v.ya_voto]
        votos_en_urna = len(self.casilla.urna['Presidencia'])
        dobles_rechazados = self.casilla.incidentes['Intento de doble voto']
        print(f'\nCiudadanos que salieron a votar: {len(self.votantes)}')
        print(f'Ciudadanos que votaron: {len(votaron)}')
        if self.MODO == 'jornada':
            print(f'Participación: {len(votaron) / self.LISTA_NOMINAL:.1%} (lista nominal {self.LISTA_NOMINAL})')
        print(f'Boletas en urna por elección: {votos_en_urna}')
        print(f'Intentos dobles rechazados: {dobles_rechazados}')
        print(f'Fila más larga: {self.casilla.max_fila}')
        if votaron:
            espera_promedio = sum((v.espera for v in votaron)) / len(votaron)
            print(f'Espera promedio: {espera_promedio:.2f} min')
        print('\nESTADOS FINALES')
        for estado, cantidad in Counter((v.estado for v in self.votantes)).most_common():
            print(f'{estado:<40} {cantidad}')
        print('\nETAPAS DE LA CASILLA')
        print(f'Apertura: {self.hora(self.casilla.apertura)}')
        print(f'Inicio escrutinio: {self.hora(self.casilla.inicio_escrutinio)}')
        print(f'Fin escrutinio: {self.hora(self.casilla.fin_escrutinio)}')
        print(f'Acta al PREP: {self.hora(self.casilla.hora_prep)}')
        print(f'Estado PREP: {self.casilla.estado_prep}')
        print(f'Votos perdidos: {self.casilla.votos_perdidos}')
        print('\nINCIDENTES')
        for nombre, cantidad in self.casilla.incidentes.most_common():
            print(f'{nombre:<30} {cantidad}')
        print(f'Recuentos por protesta: {self.casilla.recuentos}')
        if self.casilla.resultados:
            print('\nRESULTADOS POR ELECCIÓN')
            for eleccion, conteo in self.casilla.resultados.items():
                print(f'\n{eleccion}')
                for partido in PARTIDOS:
                    print(f'  {PARTIDOS[partido]}: {conteo[partido]}')
                print(f"  Coalición doble marca: {conteo['PTA+FN']}")
                print(f"  Votos nulos: {conteo['Nulos']}")
                print(f"  No registrados: {conteo['No registrado']}")
                candidaturas = {'Coalición Taco-Nopal': conteo['PTA'] + conteo['FN'] + conteo['PTA+FN'], 'Movimiento Tapatío': conteo['MT'], 'Alianza Jalisco Verde': conteo['AJV']}
                ganador = max(candidaturas, key=candidaturas.get)
                print(f'  GANADOR: {ganador}')
        elif self.casilla.robada:
            print('\nLos Minions robaron el material electoral.')
            print('No hay resultados disponibles.')
        else:
            print('\nNo se completó el escrutinio.')
        
        self.exportar_resultados_graficas()

        with open('eventos_unity.json', 'w', encoding='utf-8') as archivo:
            json.dump(sorted(self.eventos_unity, key=lambda evento: evento['t_min']), archivo, ensure_ascii=False, indent=2)

        print(f'\n{len(self.eventos_unity)} eventos guardados en eventos_unity.json')
        print(f'{len(self.mensajes)} mensajes entre agentes guardados en mensajes_agentes.csv:',
              dict(Counter(m[4] for m in self.mensajes)))
        print('\nSIMULACIÓN FINALIZADA')

    def estado_unity(self):
        return {'t_min': self.t_min, 'hora': self.hora(self.t_min), 'running': self.running, 'metricas': self.metricas(), 'fila_verificacion': [v.id for v in self.fila_verificacion], 'fila_mampara': [v.id for v in self.fila_mampara], 'verificadores_libres': self.verificadores.copy(), 'mamparas_libres': self.mamparas.copy(), 'votantes': [{'id': v.id, 'estado': v.estado, 'estres': v.estres} for v in self.votantes]}
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--modo', choices=['demo', 'jornada'], default='demo')
    parser.add_argument('--seed', type=int, default=3)
    args = parser.parse_args()
    modelo = ModeloElectoral(modo=args.modo, seed=args.seed)
    while modelo.running:
        modelo.step()
    modelo.resultados_finales()
    modelo.datacollector.get_model_vars_dataframe().to_csv('metricas_mesa.csv', index=False)
