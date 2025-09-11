function AGV_Simple()
% AGV_Simple - Unicycle AGV con I/O via wrapper (get_initial_inputs/get_input/send_output)

    % 0) Wrapper e handshake iniziale
    wrapper = SimulationWrapperInteractive();   % usa la tua classe del wrapper
    init    = wrapper.get_initial_inputs();     % static params forniti dal client

    % --- Parametri iniziali con fallback robusto ---
    DT        = init.initial.DT;    % passo di simulazione [s]
    MAX_STEPS = init.initial.MAX_STEPS;      % iterazioni
    PAUSE_IO  = init.initial.PAUSE_IO;     % sleep per evitare spin
    AGV_ID    = init.initial.AGV_ID; 
    TOL       = init.initial.WAYPOINT_TOL;   % tolleranza arrivo [m]

    % Stato iniziale
    pose0     = init.initial.INIT_POSE;          % struct con x,y,theta
    x  = pose0.x;  y = pose0.y;  th = pose0.theta;    % [m], [rad]
    v  = 0.0;                                          % velocità [m/s]
    soc= 1.0;                                          % 0..1
    speed_cap = init.initial.SPEED_CAP_DEFAULT;  % [m/s]
    load_kg   = init.initial.LOAD_KG_DEFAULT; % [kg]

    % Target corrente (se non arriva subito nulla dai get_input)
    tgt0      = init.initial.TARGET_INITIAL; % struct con x,y
    tx = tgt0.x;  ty = tgt0.y;

    % 1) main loop
    for step = 1:MAX_STEPS
        sim_time = step * DT;

        % 1.1) prova a leggere un frame dinamico (può essere vuoto)
        data_in = wrapper.get_input();
        if isstruct(data_in)
            if isfield(data_in, "target")
                if isfield(data_in.target, "x"), tx = data_in.target.x; end
                if isfield(data_in.target, "y"), ty = data_in.target.y; end
            end
            if isfield(data_in, "speed_cap"), speed_cap = data_in.speed_cap; end
            if isfield(data_in, "load_kg"),   load_kg   = data_in.load_kg;   end
        end

        % 1.2) controllo e integrazione (unicycle semplice)
        dx = tx - x;  dy = ty - y;
        dist = hypot(dx, dy);
        desired_th = atan2(dy, dx);
        e_th = wrap_to_pi(desired_th - th);

        omega = 2.0 * e_th;                         % P control heading
        v_ref = min(speed_cap, 1.5);                % cap di sicurezza
        tau_v = 0.4;                                % costante tempo velocità
        v     = v + (v_ref - v)*(DT/tau_v);         % 1° ordine verso v_ref

        th = th + omega * DT;
        x  = x  + v * cos(th) * DT;
        y  = y  + v * sin(th) * DT;

        % 1.3) consumo energetico rozzo
        P_watt = 80 + 40*v + 0.5*load_kg;          % modello fittizio
        E_kWh_s = (P_watt/1000);                   % kWh/s
        batt_kWh = pick(init, "BATTERY_KWH", 2.0);
        soc = max(0, soc - (E_kWh_s * DT) / batt_kWh);

        reached = dist <= TOL;

        % 1.4) output telemetria
        out = struct( ...
            "status",            "ok", ...
            "sim_time",          sim_time, ...
            "agv_id",            AGV_ID, ...
            "pose",              struct("x",x,"y",y,"theta",th), ...
            "v",                 v, ...
            "battery_soc",       soc, ...
            "target",            struct("x",tx,"y",ty), ...
            "reached_waypoint",  reached ...
        );
        wrapper.send_output(out);
        pause(PAUSE_IO);

        % 1.5) opzionale: se vuoi fermarti quando arrivi
        if reached && pick(init, "STOP_ON_REACH", false)
            break;
        end
    end

    wrapper.send_completed();

    % ---------- helper locali ----------
    function val = pick(s, field, def)
        if isstruct(s) && isfield(s, field), val = s.(field); else, val = def; end
    end
    function a = wrap_to_pi(a)
        % equivalente a wrapToPi senza toolbox
        a = mod(a + pi, 2*pi) - pi;
    end
end
