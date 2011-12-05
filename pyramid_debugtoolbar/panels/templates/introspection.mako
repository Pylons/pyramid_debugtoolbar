<h4>
<table>
	% for category_name, entries in categorized:
		<th><h4>${category_name.capitalize()}</h4></th>
        % for entry in entries:
          <% intro = entry['introspectable'] %>
        <tr>
           <td>
               <h5><a name="${intro.category_name}${intro.discriminator_hash}">${intro.type_name} ${intro.title}</a></h5>
               <dl>
               % for k, v in sorted(intro.items()):
                  % if v:
                    <dt>${k}</dt><dd>${debug_repr(v)|n}</dd>
                  % endif
               % endfor
              </dl>
           <h6>Source</h6>
           <code>${nl2br(str(intro.action_info))|n}</code>
           % if entry['related']:
               <h7>References</h7>
               <ul>
               % for ref in entry['related']:
                   <li>
                   <a href="#${ref.category_name}${ref.discriminator_hash}">${ref.type_name} ${ref.title}</a>
                  </li>
               % endfor
               </ul>
           % endif
           </td>
		</tr>
	    % endfor
     % endfor
</table>
