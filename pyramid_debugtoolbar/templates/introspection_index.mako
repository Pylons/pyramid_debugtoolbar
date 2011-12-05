<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
  "http://www.w3.org/TR/html4/loose.dtd">
<html>
  <head>
    <title>Pyramid Debug Toolbar Introspector</title>
    <link rel="stylesheet" href="${static_path}css/introspection.css" 
          type="text/css">
  </head>
  <body>
  <h1>Pyramid Configuration Introspection</h1>
  <table>
	% for category_name, entries in categorized:
		<th><h2>${category_name.capitalize()}</h2></th>
        % for entry in entries:
        <tr>
           <td>
               <h3><a name="${entry['introspectable'].category_name}${entry['introspectable'].discriminator_hash}">${entry['introspectable'].type_name} ${entry['introspectable'].title}</a></h3>
               <dl>
               % for k, v in sorted(entry['introspectable'].items()):
                  % if v:
                    <dt>${k}</dt><dd>${debug_repr(v)|n}</dd>
                  % endif
               % endfor
              </dl>
           <h4>Source</h4>
           <pre>${nl2br(str(entry['introspectable'].action_info))|n}</pre>
           % if entry['related']:
               <h4>References</h4>
               <ul>
               % for ref in entry['related']:
                   <li>
                   <h5><a href="#${ref.category_name}${ref.discriminator_hash}">${ref.type_name} ${ref.title}</a></h5>
                  </li>
               % endfor
               </ul>
           % endif
           </td>
		</tr>
	    % endfor
     % endfor
    </table>
</body>
</html>
